from __future__ import annotations

from argparse import ArgumentError
from typing import TYPE_CHECKING
from pathlib import Path

from argx import Namespace
from simpleconf import ProfileConfig
from pipen import plugin
from pipen.defaults import CONFIG_FILES
from pipen.utils import copy_dict, get_logger, is_loading_pipeline

from .version import __version__
from .parser_ import Parser

if TYPE_CHECKING:  # pragma: no cover
    from pipen import Pipen

logger = get_logger("args", "info")
# Save the warnings to print them after the pipeline is initialized
# So that they are printed after the logo and the pipeline info
warns = []


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

        config = {"plugin_opts": {}, "template_opts": {}, "scheduler_opts": {}}
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
        parsed = parser.parse_args()
        # Load configs by profile
        if parsed.profile is not None:  # pragma: no cover
            pipen.profile = parsed.profile
            init_config = ProfileConfig.load(
                {"default": pipen.config},
                *CONFIG_FILES,
                ignore_nonexist=True,
            )
            init_config = ProfileConfig.use_profile(
                init_config,
                parsed.profile,
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
            if getattr(parsed, key, None) is not None:
                config[key] = getattr(parsed, key)

        # The original name
        pipen_name = pipen.name
        # The default outdir
        pipen_outdir = Path(f"./{pipen_name}-output").resolve()
        # The default workdir
        pipen_workdir = Path(
            f"./{pipen.config['workdir']}/{pipen_name}"
        ).resolve()

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
                pipen.outdir = Path(f"./{pipen.name}-output").resolve()
            else:
                # otherwise, use it
                pipen.outdir = parsed.outdir.resolve()
        elif parsed.outdir is not None and parsed.outdir != pipen.outdir:
            # The outdir is set by higher priority, and a value is passed by
            # arguments, so we need to warn the user that the value from
            # arguments will be ignored
            warns.append(
                "[red](!)[/red] Pipeline `outdir` is given by a higher "
                "priority (`Pipen.outdir`, or `Pipen(outdir=...)`), "
                "ignore the value from cli arguments",
            )

        # Update the workdir
        if pipen.workdir is None or pipen.workdir.resolve() == pipen_workdir:
            # The workdir is still some default values, that means it is not set
            # by higher priority (Pipen.workdir, or Pipen(workdir=...))
            # So we can use the value from arguments
            if parsed.workdir is not None:
                # If it is passed by arguments, use it
                workdir = parsed.workdir
            else:
                # Otherwise, use the name to infer the workdir
                workdir = Path(pipen.config['workdir'])
            pipen.workdir = workdir.joinpath(pipen.name).resolve()
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

        for key in ("plugin_opts", "template_opts", "scheduler_opts"):
            old = copy_dict(config[key] or {}, 3)
            old.update(getattr(parsed, key, None) or {})
            config[key] = old

        pipen.config.update(config)

        if parser.flatten_proc_args is True:
            parsed = Namespace(**{pipen.procs[0].name: parsed})

        for proc in pipen.procs:
            proc_args = vars(getattr(parsed, proc.name))
            if (
                "in" in proc_args
                and not all(v is None for v in vars(proc_args["in"]).values())
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
                            key: (
                                val * maxlen
                                if len(val) == 1 and maxlen > 1
                                else val
                            )
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
        for wn in warns:  # pragma: no cover
            logger.warning(wn)
