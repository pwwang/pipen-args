from __future__ import annotations

import json
import re
from argparse import ArgumentError
from typing import TYPE_CHECKING
from pathlib import Path

from argx import Namespace
from argx.action import HelpAction, NamespaceAction
from argx.parser import _NamespaceArgumentGroup
from simpleconf import ProfileConfig
from pipen import plugin
from pipen.defaults import CONFIG_FILES
from pipen.utils import copy_dict, get_logger, is_loading_pipeline, get_marked

from .version import __version__
from .defaults import FLATTEN_PROC_ARGS, DUMP_ARGS
from .parser_ import Parser

if TYPE_CHECKING:  # pragma: no cover
    from argparse import Action, ArgumentParser
    from pipen import Pipen

logger = get_logger("args", "info")
# Save the warnings to print them after the pipeline is initialized
# So that they are printed after the logo and the pipeline info
warns = []
infos = []

# valid toml key
VALID_TOML_KEY = re.compile(r"^[a-zA-Z0-9_-]+$")


def _dump_dict(d: dict) -> str:
    """Dump a dictionary into a string"""
    out = []
    for key, value in d.items():
        if not VALID_TOML_KEY.match(key) and "-" not in key:
            key = f'"{key}"'
        if isinstance(value, dict):
            out.append(f"{key} = {_dump_dict(value)}")
        else:
            out.append(f"{key} = {json.dumps(value)}")
    out = ", ".join(out)
    return f"{{ {out} }}"


def _sort_actions(
    actions: list[Action],
    procgroups: dict,
    procs: dict,
) -> list[Action]:
    """Sort the actions"""
    indexes = {}
    for action in actions:
        if isinstance(action, HelpAction) or action.dest in (
            "workdir",
            "dirsig",
            "lang",
        ):
            action.index = None
            continue

        if "." in action.dest:
            part = action.dest.rpartition(".")[0]
            if part in indexes:
                if isinstance(action, NamespaceAction):
                    indexes[action.dest] = indexes[part] + 900
                else:
                    indexes[action.dest] = indexes[part] + 1

                action.index = indexes[action.dest]
                continue

            maybeproc = action.dest.split(".")[0]

            if maybeproc in procgroups:
                if isinstance(action, NamespaceAction):
                    indexes[action.dest] = procgroups[maybeproc]["base"] + 90000
                else:
                    indexes[action.dest] = procgroups[maybeproc]["base"] + 1
            elif maybeproc in procs:
                if isinstance(action, NamespaceAction):
                    indexes[action.dest] = procs[maybeproc]["base"] + 9000
                else:
                    indexes[action.dest] = procs[maybeproc]["base"] + 1
            else:
                indexes[action.dest] = 1000

        elif action.dest in procgroups:
            indexes[action.dest] = procgroups[action.dest]["base"]
        elif action.dest in procs:
            indexes[action.dest] = procs[action.dest]["base"]
        elif isinstance(action, NamespaceAction):
            indexes[action.dest] = 9000
        else:
            indexes[action.dest] = 1

        action.index = indexes[action.dest]

    return sorted(
        [action for action in actions if action.index],
        key=lambda x: x.index,
    )


def _procs_and_groups(
    parser: ArgumentParser,
    args_flatten: bool,
    proc0: str | None,
    pg0: str | None,
) -> tuple[dict, dict]:
    """Get the process groups and processes"""
    procgroups = {}
    procs = {}
    if args_flatten and proc0:
        default_group = {
            "procs": [],
            "used": False,
            "base": (len(procgroups) + 1) * 1000000,
        }
        default_proc = {
            "group": None,
            "used": False,
            "base": (len(procs) + 1) * 10000,
        }
        if pg0:
            procgroups.setdefault(pg0, default_group)
            procgroups[pg0]["procs"] = [proc0]
            procs.setdefault(proc0, default_proc)
            procs[proc0]["group"] = pg0
            procs[proc0]["base"] += procgroups[pg0]["base"]
        else:
            procs[proc0] = default_proc
    else:
        for group in parser._action_groups:
            if not isinstance(group, _NamespaceArgumentGroup):
                continue

            default_group = {
                "procs": [],
                "used": False,
                "base": (len(procgroups) + 1) * 1000000,
            }
            default_proc = {
                "group": None,
                "used": False,
                "base": (len(procs) + 1) * 10000,
            }

            if group.title.startswith("Process Group <"):
                procgroups.setdefault(group.name, default_group)
            elif "/" in group.title:
                pg = group.title[9:].split("/", 1)[0]
                procgroups.setdefault(pg, default_group)
                procgroups[pg]["procs"].append(group.name)
                procs.setdefault(group.name, default_proc)
                procs[group.name]["group"] = pg
                procs[group.name]["base"] += procgroups[pg]["base"]
            else:
                procs[group.name] = default_proc

    return procgroups, procs


def dump_args(
    parser: Parser,
    parsed: Namespace,
    dumped_file: Path,
    args_flatten: bool,
    proc0: str | None,
    pg0: str | None,
) -> None:
    """Dump the parsed arguments into a dictionary

    Args:
        parser: The parser instance
        parsed: The parsed arguments
        dumped_file: The path to the TOML file
    """
    out = {}
    parsed_dict = vars(parsed)
    NS_VAL = object()

    procgroups, procs = _procs_and_groups(parser, args_flatten, proc0, pg0)

    # Access the argument groups through the underlying argparser
    for action in _sort_actions(parser._actions, procgroups, procs):
        key = action.dest
        value = parsed_dict.get(key)
        if args_flatten and proc0 and key.split(".")[0] in ("envs", "in", "out"):
            key = f"{proc0}.{key}"

        if "." in key:
            maybeproc, rest = key.split(".", 1)

            if maybeproc in procgroups:
                if not procgroups[maybeproc]["used"]:
                    procgroups[maybeproc]["used"] = True
                    out[maybeproc] = NS_VAL
                    out[f"__help_{maybeproc}"] = "\n".join(
                        (
                            f"+{'-' * 78}+",
                            f"| {'Argument for process group: '} {maybeproc:<47} |",
                            f"+{'-' * 78}+",
                        )
                    )
            elif maybeproc in procs:
                if not procs[maybeproc]["used"]:
                    procs[maybeproc]["used"] = True
                    out[maybeproc] = NS_VAL
                    if procs[maybeproc]["group"]:
                        procname = f"{procs[maybeproc]['group']}/{maybeproc}"
                    else:
                        procname = maybeproc
                    out[f"__help_{maybeproc}"] = "\n".join(
                        (
                            f"+{'-' * 78}+",
                            f"| {'Argument for process: '} {procname:<53} |",
                            f"+{'-' * 78}+",
                        )
                    )

            ns = rest.split(".")[0]
            if ns in ("in", "out", "lang", "dirsig", "order"):
                continue

        if isinstance(action, NamespaceAction):
            # Skip dumping values for Namespace actions
            out[key] = NS_VAL
            if action.help:
                out[f"__help_{key}"] = action.help
        else:
            out[key] = value
            if action.help:
                out[f"__help_{key}"] = action.help

    dumped_file.parent.mkdir(parents=True, exist_ok=True)
    with open(dumped_file, "w") as f:
        for key, value in out.items():
            if key.startswith("__help_"):
                continue

            help_key = f"__help_{key}"
            if help_key in out:
                for line in out[help_key].splitlines():
                    f.write(f"# {line}\n")

            if value is NS_VAL:
                f.write(f"[{key}]\n\n")
            else:
                key = key.split(".")[-1]
                if value is None:
                    f.write(f"## {key} = None\n\n")
                elif isinstance(value, Path):
                    f.write(f"{key} = {str(value)!r}\n\n")
                elif isinstance(value, dict):
                    f.write(f"{key} = {_dump_dict(value)}\n\n")
                else:
                    f.write(f"{key} = {json.dumps(value)}\n\n")


class ArgsPlugin:
    """Automatically parse arguments and load configs for pipen pipelines"""

    name = "args"
    priority = -9
    version = __version__

    @plugin.impl
    async def on_init(pipen: Pipen) -> None:
        """Parse and update the config"""
        if is_loading_pipeline():  # pragma: no cover
            return

        args_flatten = pipen._kwargs["plugin_opts"].get(
            "args_flatten",
            FLATTEN_PROC_ARGS,
        )

        config: dict = {"plugin_opts": {}, "template_opts": {}, "scheduler_opts": {}}
        config["plugin_opts"]["args_hide"] = False
        parser = Parser()
        # Init the parser
        try:
            parser.init(pipen)
        except ArgumentError:
            # The parser is initialized in another pipeline
            raise ValueError(
                "`pipen-args` can only be used in one pipeline at a time."
            ) from None

        # Parse the args
        parsed = parser.parse_args(_internal=True)

        # Warn if args_hide, args_group, args_flatten are passed
        if parsed.plugin_opts and "args_hide" in parsed.plugin_opts:
            warns.append(
                "[red](!)[/red] `plugin_opts.args_hide` should not be passed "
                "via command line or config file via `@configfile`"
            )
            del parsed.plugin_opts["args_hide"]
        if parsed.plugin_opts and "args_group" in parsed.plugin_opts:
            warns.append(
                "[red](!)[/red] `plugin_opts.args_group` should not be passed "
                "via command line or config file via `@configfile`"
            )
            del parsed.plugin_opts["args_group"]
        if parsed.plugin_opts and "args_flatten" in parsed.plugin_opts:
            warns.append(
                "[red](!)[/red] `plugin_opts.args_flatten` should not be passed "
                "via command line or config file via `@configfile`"
            )
            del parsed.plugin_opts["args_flatten"]

        profile = None
        # Load configs by profile
        if pipen.profile and pipen.profile != "default":
            if parsed.profile is not None:
                warns.append(
                    "[red](!)[/red] `profile` is given by a higher priority, "
                    "ignore the value from cli arguments"
                )
            profile = pipen.profile
        elif parsed.profile is not None:
            profile = parsed.profile

        if profile and profile != "default":
            pipen.profile = profile
            init_config = ProfileConfig.load(
                {"default": pipen.config},
                *CONFIG_FILES,
                ignore_nonexist=True,
            )
            init_config = ProfileConfig.use_profile(
                init_config,
                profile,
                copy=True,
            )
            config.update(init_config)

        for key in (
            "loglevel",
            "cache",
            "dirsig",
            "lang",
            "error_strategy",
            "num_retries",
            "forks",
            "submission_batch",
            "scheduler",
            "plugins",
        ):
            if getattr(parsed, key) is not None:
                if key in pipen._kwargs:
                    warns.append(
                        f"[red](!)[/red] `{key}` is given by a higher priority, "
                        "ignore the value from cli arguments"
                    )
                    setattr(parsed, key, pipen._kwargs[key])

                config[key] = getattr(parsed, key)

        # The original name
        pipen_name = pipen.name
        # The default outdir
        pipen_outdir = Path(f"./{pipen_name}-output").absolute()
        # The default workdir
        pipen_workdir = Path(f"./{pipen.config['workdir']}/{pipen_name}").absolute()

        # Update the name
        if parsed.name not in (None, pipen_name):
            pipen.name = parsed.name

        # Update the outdir
        if pipen.outdir in (None, pipen_outdir):
            # The outdir is still some default values, that means it is not set
            # by higher priority (Pipen.outdir, or Pipen(outdir=...))
            # So we can use the value from arguments
            if parsed.outdir == pipen.outdir:
                # if outdir is not passed from cli,
                # use the name to infer the outdir
                parsed.outdir = pipen.outdir = Path(f"./{pipen.name}-output").absolute()
            else:
                # otherwise, use it
                pipen.outdir = parsed.outdir.absolute()

        elif parsed.outdir is not None and parsed.outdir != pipen.outdir:
            # The outdir is set by higher priority, and a value is passed by
            # arguments, so we need to warn the user that the value from
            # arguments will be ignored
            warns.append(
                "[red](!)[/red] Pipeline `outdir` is given by a higher "
                "priority (`Pipen.outdir`, or `Pipen(outdir=...)`), "
                "ignore the value from cli arguments",
            )
            parsed.outdir = pipen.outdir

        # Update the workdir
        if pipen.workdir is None or pipen.workdir.absolute() == pipen_workdir:
            # The workdir is still some default values, that means it is not set
            # by higher priority (Pipen.workdir, or Pipen(workdir=...))
            # So we can use the value from arguments
            if parsed.workdir is not None:
                # If it is passed by arguments, use it
                workdir = parsed.workdir
            else:
                # Otherwise, use the name to infer the workdir
                workdir = Path(pipen.config["workdir"])

            parsed.workdir = pipen.workdir = workdir.joinpath(pipen.name).absolute()
            pipen.workdir.mkdir(parents=True, exist_ok=True)

        elif parsed.workdir is not None and parsed.workdir != pipen.workdir:
            # The workdir is set by higher priority, and a value is passed by
            # arguments, so we need to warn the user that the value from
            # arguments will be ignored
            warns.append(
                "[red](!)[/red] Pipeline `workdir` is given by a higher "
                "priority (Pipen.workdir, or Pipen(workdir=...)), "
                "ignore the value from cli arguments",
            )
            parsed.workdir = pipen.workdir

        for key in ("plugin_opts", "template_opts", "scheduler_opts"):
            old = copy_dict(config[key] or {}, 99)
            old.update(getattr(parsed, key) or {})
            config[key] = old

            for k, v in pipen._kwargs[key].items():
                if k in old:
                    warns.append(
                        f"[red](!)[/red] `{key}.{k}` is given by a higher "
                        "priority, ignore the value from cli arguments"
                    )

                config[key][k] = v

            setattr(parsed, key, config[key])

        pipen.config.update(config)

        # args_dump should be able to be passed from command line
        args_dump = pipen.config.plugin_opts.get("args_dump", DUMP_ARGS)

        if args_dump:
            args_dump_file = pipen.outdir / "args.toml"
            proc0 = pipen.procs[0] if pipen.procs else None
            dump_args(
                parser,
                parsed,
                args_dump_file,
                args_flatten and len(pipen.procs) == 1,
                proc0.name if proc0 else None,
                get_marked(proc0, "procgroup") if proc0 else None,
            )
            infos.append(f"All arguments are dumped to {args_dump_file}")

        if parser.flatten_proc_args is True:
            parsed = Namespace(**{pipen.procs[0].name: parsed})

        for proc in pipen.procs:
            proc_args = vars(getattr(parsed, proc.name))
            if "in" in proc_args and not all(
                v is None for v in vars(proc_args["in"]).values()
            ):
                if proc.input_data is not None:
                    warns.append(
                        f"[red](!)[/red] [{proc.name}] `input_data` is given, "
                        "ignore input from cli arguments"
                    )
                else:
                    from pandas import DataFrame
                    from pandas.core.dtypes.api import is_scalar

                    indata = vars(proc_args["in"])
                    for key, val in indata.items():
                        if is_scalar(val):
                            indata[key] = [val]

                    maxlen = max(map(len, indata.values()))
                    input_data = DataFrame(
                        {
                            key: (val * maxlen if len(val) == 1 and maxlen > 1 else val)
                            for key, val in indata.items()
                            if val is not None and len(val) > 0
                        }
                    )
                    # only when input data is given and not all None
                    if input_data.shape[0] > 0:
                        proc.input_data = input_data

            if (
                "envs" in proc_args
                and proc.envs is not None
                and proc_args["envs"] is not None
            ):
                proc_envs = (
                    vars(proc_args["envs"])
                    if isinstance(proc_args["envs"], Namespace)
                    else proc_args["envs"]
                )
                proc.envs.update(proc_envs)

            for key in (
                "cache",
                "dirsig",
                "lang",
                "error_strategy",
                "num_retries",
                "forks",
                "scheduler",
                "submission_batch",
            ):
                if proc_args.get(key) is not None:
                    setattr(proc, key, proc_args[key])

            for key in ("plugin_opts", "scheduler_opts"):
                if key in proc_args:
                    if proc_args[key]:
                        proc_opts = getattr(proc, key, None)
                        if proc_opts is None:
                            setattr(proc, key, {})
                        getattr(proc, key).update(proc_args[key])

    @plugin.impl
    async def on_start(pipen: Pipen) -> None:
        """Print warnings"""
        for wn in warns:
            logger.warning(wn)
        for info in infos:
            logger.info(info)
