from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

from argx import Namespace
from simpleconf import ProfileConfig
from pipen import plugin
from pipen.defaults import CONFIG_FILES
from pipen.utils import copy_dict, get_logger

from .version import __version__
from .parser_ import Parser

if TYPE_CHECKING:  # pragma: no cover
    from pipen import Pipen

logger = get_logger("args", "info")


class ArgsPlugin:
    """Automatically parse arguments and load configs for pipen pipelines"""
    name = "args"
    version = __version__

    @plugin.impl
    async def on_init(pipen: Pipen) -> None:
        """Parse and update the config"""
        config = pipen.config
        config.plugin_opts.args_hide = False

        parser = Parser()
        # Init the parser
        parser.init(pipen)

        # Parse the args
        parsed = parser.parse_args()
        # Load configs by profile
        if parsed.profile is not None:  # pragma: no cover
            pipen.profile = parsed.profile
            try:
                fileconfs = ProfileConfig.load(
                    *CONFIG_FILES,
                    ignore_nonexist=True,
                )
            except KeyError:  # no default profile
                pass
            else:
                ProfileConfig.use_profile(
                    fileconfs,
                    pipen.profile,
                )
                config.update(fileconfs)

        # Save original outdir to see if it's changed
        pipen_outdir = pipen.outdir
        if parsed.outdir is not None:
            pipen.outdir = parsed.outdir.resolve()

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

        if parsed.name not in (None, pipen.name):
            pipen.name = parsed.name
            pipen.workdir = Path(config["workdir"]) / pipen.name
            pipen.workdir.mkdir(parents=True, exist_ok=True)
            if parsed.outdir in (None, pipen_outdir):
                pipen.outdir = Path(
                    f"./{pipen.name}_results"
                ).resolve()

        for key in ("plugin_opts", "template_opts", "scheduler_opts"):
            old = copy_dict(config[key] or {}, 3)
            old.update(getattr(parsed, key, None) or {})
            config[key] = old

        if parser.flatten_proc_args is True:
            parsed = Namespace(**{pipen.procs[0].name: parsed})

        for proc in pipen.procs:
            proc_args = vars(getattr(parsed, proc.name))
            if (
                "in" in proc_args
                and not all(v is None for v in vars(proc_args["in"]).values())
            ):
                if proc.input_data is not None:
                    logger.warning(
                        "[red]![%s] input_data is given, ignore input from "
                        "parsed arguments[/red]",
                        proc.name,
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
                if key in proc_args:
                    setattr(proc, key, proc_args[key])

            for key in ("plugin_opts", "scheduler_opts"):
                if key in proc_args:
                    if proc_args[key]:
                        proc_opts = getattr(proc, key, None)
                        if proc_opts is None:
                            setattr(proc, key, {})
                        getattr(proc, key).update(proc_args[key])
