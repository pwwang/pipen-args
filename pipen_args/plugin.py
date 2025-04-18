from __future__ import annotations

from argparse import ArgumentError
from typing import TYPE_CHECKING
from pathlib import Path

from argx import Namespace
from simpleconf import ProfileConfig
from pipen import plugin
from pipen.defaults import CONFIG_FILES
from pipen.utils import copy_dict, get_logger, is_loading_pipeline, update_dict

from .version import __version__
from .defaults import DUMP_ARGS
from .parser_ import Parser
from .utils import dump_args

if TYPE_CHECKING:  # pragma: no cover
    from pipen import Pipen

logger = get_logger("args", "info")
# Save the warnings to print them after the pipeline is initialized
# So that they are printed after the logo and the pipeline info
warns = []
infos = []


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
        plugin_opts_action = parser.get_action("plugin_opts")
        plugin_opts_default = plugin_opts_action.default if plugin_opts_action else {}
        # Warn if args_hide, args_group, args_flatten are passed
        if parsed.plugin_opts and "args_hide" in parsed.plugin_opts and (
            parsed.plugin_opts["args_hide"] != plugin_opts_default.get("args_hide")
        ):
            warns.append(
                "[red](!)[/red] `plugin_opts.args_hide` should not be passed "
                "via command line or config file via `@configfile`"
            )
            del parsed.plugin_opts["args_hide"]

        if parsed.plugin_opts and "args_group" in parsed.plugin_opts and (
            parsed.plugin_opts["args_group"] != plugin_opts_default.get("args_group")
        ):
            warns.append(
                "[red](!)[/red] `plugin_opts.args_group` should not be passed "
                "via command line or config file via `@configfile`"
            )
            del parsed.plugin_opts["args_group"]

        if parsed.plugin_opts and "args_flatten" in parsed.plugin_opts and (
            parsed.plugin_opts["args_flatten"]
            != plugin_opts_default.get("args_flatten")
        ):
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
            value = getattr(parsed, key)
            if value is not None:
                if key in pipen._kwargs:
                    if (
                        value != parser.get_action(key).default
                        and value != pipen._kwargs[key]
                    ):
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
            action = parser.get_action(key)

            value = getattr(parsed, key) or {}
            old = copy_dict(config[key] or {}, 99)
            default = action.default if action else None
            default = default or config[key] or {}
            old.update(value)
            config[key] = old

            for k, v in pipen._kwargs[key].items():
                if k in old and old[k] != default.get(k) and old[k] != v:
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
            dump_args(
                parser,
                parsed,
                args_dump_file,
                pipen.procs,
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
                # proc.envs.update(proc_envs)
                proc.envs = update_dict(
                    proc.envs,
                    proc_envs,
                    depth=proc.envs_depth or 1,
                )

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
