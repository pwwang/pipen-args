"""Command line argument parser for pipen"""

import sys
from io import StringIO
from pathlib import Path

from pardoc import google_parser
from pardoc.parsed import ParsedItem, ParsedPara
from diot import Diot
from pipen import plugin
from pipen.defaults import CONFIG_FILES
from pipen.utils import _logger_handler, copy_dict
from pyparam import Params, defaults
from pyparam.utils import cast_to
from simpleconf import ProfileConfig, Config

from slugify import slugify

__version__ = "0.3.3"

# Allow type to be overriden from command line
defaults.PARAM.type_frozen = False
defaults.CONSOLE_WIDTH = 99

PARAM_DESCRS = {
    "profile": (
        "The default profile from the configuration to run the "
        "pipeline. This profile will be used unless a profile is "
        "specified in the process or in the .run method of pipen."
    ),
    "lang": "The language interpreter to use for the pipeline/process.",
    "outdir": "The output directory of the pipeline",
    "loglevel": (
        "The logging level for the main logger, only takes effect "
        "after pipeline is initialized."
    ),
    "cache": "Whether enable caching for processes.",
    "dirsig": (
        "The depth to check the Last Modification Time of a directory.",
        "Since modifying the content won't change its LMT.",
    ),
    "error_strategy": (
        "How we should deal with job errors.",
        " - `ignore`: Let other jobs keep running. "
        "But the process is still failing when done.",
        " - `halt`: Halt the pipeline, other running jobs will be " "killed.",
        " - `retry`: Retry this job on the scheduler system.",
    ),
    "num_retries": "How many times to retry the job when failed.",
    "forks": "How many jobs to run simultaneously by the scheduler.",
    "submission_batch": (
        "How many jobs to submit simultaneously to the scheduler system."
    ),
    "name": (
        "The name for the pipeline, "
        "will affect the default workdir and outdir.",
    ),
    "scheduler": "The scheduler to run the jobs.",
    "scheduler_opts": (
        "The default scheduler options. Will update to the default one."
    ),
    "plugins": (
        "A list of plugins to only enabled or disabled for this pipeline.",
        "To disable plugins, use `no:<plugin_name>`",
    ),
    "plugin_opts": "Plugin options. Will update to the default.",
    "template_opts": "Template options. Will update to the default.",
}

HIDDEN_ARGS = (
    "scheduler_opts",
    "plugin_opts",
    "template_opts",
    "dirsig",
    "cache",
    "export",
    "forks",
    "error_strategy",
    "num_retries",
    "loglevel",
    "plugins",
    "submission_batch",
)


def _annotate_process(proc):
    """Annotate the process with docstrings"""
    parsed = google_parser.parse(proc.__doc__ or "")
    keys = ("Input", "Output", "Envs")

    out = {}
    for key in keys:
        out[key] = {}
        if key not in parsed:
            continue
        for item in parsed[key].section:
            if not isinstance(item, ParsedItem):  # pragma: no cover
                continue

            out[key][item.name] = [item.desc]
            if item.more:
                for moreitem in item.more:
                    if not isinstance(moreitem, ParsedPara):
                        continue
                    out[key][item.name].extend(moreitem.lines)

    return out


def _doc_to_summary(docstr):
    """Get the first line of docstring as summary"""
    out = []
    for i, line in enumerate(docstr.splitlines()):
        line = line.strip()
        if not line and i > 0:
            break
        out.append(line)
    return " ".join(out)


class Args(Params):
    """Subclass of Params to fit for pipen

    Args:
        pipen_opt_group: The group name to gather all the parameters on
            help page
        hidden_args: Hide some arguments in help page
    """

    INST = None

    def __new__(
        cls,
        *args,
        pipen_opt_group="PIPELINE OPTIONS",
        hidden_args=HIDDEN_ARGS,
        flatten_proc_args="auto",
        **kwargs,
    ):
        """Make class as singleton

        As we want external instantiation returns the same instance.
        """
        if cls.INST is None:
            cls.INST = super().__new__(cls)
            return cls.INST

        raise ValueError(
            "Class Args should only instantiate once. \n"
            "If you want to access the instance, use `Args.INST` or "
            "`from pipen_args import args`"
        )

    def __init__(
        self,
        *args,
        pipen_opt_group="PIPELINE OPTIONS",
        hidden_args=HIDDEN_ARGS,
        flatten_proc_args="auto",
        **kwargs,
    ):
        """Constructor"""
        if getattr(self, "_inited", False):
            return

        self.pipen_opt_group = pipen_opt_group and pipen_opt_group.upper()

        def help_callback(helps):
            helps.insert(
                None, self.pipen_opt_group, helps.pop(self.pipen_opt_group)
            )
            user_callback = kwargs.pop("help_callback", None)
            if callable(user_callback):
                user_callback(helps)

        kwargs["help_callback"] = help_callback
        super().__init__(*args, **kwargs)

        self.hidden_args = hidden_args or ()
        self.flatten_proc_args = flatten_proc_args
        self.cli_args = None
        # self.init()
        self.parsed = None
        _logger_handler.console.file = self.file = StringIO()

        self._inited = True

    def parse(self, args=None, ignore_errors=False):
        if not self.parsed:
            if ignore_errors:
                return super().parse(args, True)
            try:
                self.parsed = super().parse(args, False)
                sys.stdout.write(self.file.getvalue())
            finally:
                _logger_handler.console.file = sys.stdout
        return self.parsed

    def init(self, pipen):
        """Define arguments"""
        group_arg = {"group": self.pipen_opt_group}

        pipen.build_proc_relationships()
        if len(pipen.procs) > 1 and self.flatten_proc_args is True:
            raise ValueError(
                "Cannot flatten process arguments for multiprocess pipeline."
            )

        if len(pipen.procs) == 1 and self.flatten_proc_args == "auto":
            self.flatten_proc_args = True

        config = pipen.config
        if self.flatten_proc_args:
            config = config.copy()
            for opt in (
                "lang",
                "cache",
                "dirsig",
                "error_strategy",
                "num_retries",
                "forks",
                "submission_batch",
                "scheduler",
                "scheduler_opts",
                "plugin_opts",
            ):
                value = getattr(pipen.procs[0], opt, None)
                if value is not None:
                    config[opt] = value

        for opt, desc in PARAM_DESCRS.items():
            self.add_param(
                opt,
                default=(
                    pipen.outdir
                    if opt == "outdir"
                    else pipen.name
                    if opt == "name"
                    else {}
                    if opt.endswith("_opts")
                    else config[opt]
                    if opt != "profile"
                    else "default"
                ),
                type=str if opt == "cache" else None,
                show=opt not in self.hidden_args,
                desc=desc,
                callback=(
                    (lambda val: val and val.upper())
                    if opt == "loglevel"
                    else (
                        lambda val: (
                            val if val == "force" else cast_to(val, "bool")
                        )
                    )
                    if opt == "cache"
                    else None
                ),
                **group_arg,
            )

        if self.flatten_proc_args is True:
            self._add_proc_args(
                pipen.procs[0],
                is_start=True,
                hide=False,
                flatten=True,
            )
        else:
            for proc in pipen.procs:
                self._add_proc_args(
                    proc,
                    is_start=proc in pipen.starts,
                    hide=(
                        False
                        if not proc.plugin_opts
                        else proc.plugin_opts.get("args_hide", False)
                    ),
                    flatten=False,
                )

    def _add_proc_args(self, proc, is_start, hide, flatten):
        """Add process arguments"""
        if is_start:
            hide = False

        try:
            anno = _annotate_process(proc)
        except Exception:
            anno = {"Input": {}, "Output": {}, "Envs": {}}

        if not flatten:
            # add a namespace argumemnt for this proc
            self.add_param(
                proc.name,
                desc=_doc_to_summary(proc.__doc__ or ""),
                type="ns",
                group="PROCESSES",
            )

        else:
            # add proc's summary to params' description
            if self.desc == ["Undescribed."]:
                self.desc = []
            self.desc.append(_doc_to_summary(proc.__doc__ or ""))

        if is_start:
            self.add_param(
                "in" if flatten else f"{proc.name}.in",
                desc="Input data for the process.",
                show=False,
                argname_shorten=False,
                type="ns",
                group=f"OPTIONS FOR <{proc.name}>",
            )

            input_keys = proc.input or []
            if isinstance(input_keys, str):
                input_keys = [ikey.strip() for ikey in input_keys.split(",")]

            for input_key_type in input_keys:
                if ":" not in input_key_type:
                    input_key = input_key_type.strip()
                    # out.type[input_key_type] = ProcInputType.VAR
                else:
                    # input_key, input_type = input_key_type.split(":", 1)
                    input_key, _ = input_key_type.split(":", 1)
                    input_key = input_key.strip()
                    # input_type = input_type.strip()

                self.add_param(
                    f"in.{input_key}"
                    if flatten
                    else f"{proc.name}.in.{input_key}",
                    desc=anno["Input"].get(input_key, "Undescribed."),
                    argname_shorten=False,
                    type="list",
                    group=f"OPTIONS FOR <{proc.name}>",
                )

        if not proc.nexts:
            self.add_param(
                "out" if flatten else f"{proc.name}.out",
                desc="Output for the process (can't be overwritten, just FYI).",
                show=False,
                type="ns",
                argname_shorten=False,
                group=f"OPTIONS FOR <{proc.name}>",
            )

            for key, val in anno["Output"].items():
                self.add_param(
                    f"out.{key}" if flatten else f"{proc.name}.out.{key}",
                    desc=anno["Output"].get(key, "Undescribed."),
                    default="<awaiting compiling>",
                    type="auto",
                    show=not hide,
                    argname_shorten=False,
                    group=f"OPTIONS FOR <{proc.name}>",
                )

        self.add_param(
            "envs" if flatten else f"{proc.name}.envs",
            desc="Envs for the process.",
            argname_shorten=False,
            show=False,
            type="ns",
            group=f"OPTIONS FOR <{proc.name}>",
        )
        for key, val in (proc.envs or {}).items():
            self.add_param(
                f"envs.{key}" if flatten else f"{proc.name}.envs.{key}",
                default=val,
                show=not hide,
                desc=anno["Envs"].get(key, "Undescribed."),
                argname_shorten=False,
                group=f"OPTIONS FOR <{proc.name}>",
            )

        if not flatten:
            for key in (
                "cache",
                "dirsig",
                "lang",
                "error_strategy",
                "num_retries",
                "forks",
                "submission_batch",
            ):
                self.add_param(
                    f"{proc.name}.{key}",
                    desc=PARAM_DESCRS[key],
                    default=getattr(proc, key),
                    show=not hide and (key not in self.hidden_args),
                    argname_shorten=False,
                    group=f"OPTIONS FOR <{proc.name}>",
                )

            self.add_param(
                f"{proc.name}.export",
                desc="Whether to export output for this process.",
                show=not hide and ("export" not in self.hidden_args),
                default=not proc.nexts,
                argname_shorten=False,
                group=f"OPTIONS FOR <{proc.name}>",
            )

            for key in ("plugin_opts", "scheduler_opts"):
                self.add_param(
                    f"{proc.name}.{key}",
                    desc=PARAM_DESCRS[key],
                    show=not hide and (key not in self.hidden_args),
                    default={},
                    argname_shorten=False,
                    type="json",
                    group=f"OPTIONS FOR <{proc.name}>",
                )

            self.add_param(
                f"{proc.name}.<config>",
                desc=(
                    "Other process-level configurations.",
                    f"See [{self.pipen_opt_group}], and use --full "
                    "to see all of them",
                ),
                show=not hide,
                argname_shorten=False,
                group=f"OPTIONS FOR <{proc.name}>",
            )


def __getattr__(name: str) -> Args:
    """Instantiate the instance only on import"""
    # to avoid this function to be called twice
    if name == "__path__":
        raise AttributeError
    if name == "args":
        Args.INST = Args()
        return Args.INST
    if name == "config":
        for i, arg in enumerate(sys.argv):
            if arg == "--config":
                return Config.load(sys.argv[i + 1])
        return Diot()
    raise AttributeError


@plugin.impl
async def on_init(pipen):
    """Parse and update the config"""
    config = pipen.config
    config.plugin_opts.args_hide = False

    if Args.INST is None:
        raise ImportError(
            "[pipen-args] Args class is not instantiated. \n"
            "Either do:\n"
            "   >>> from pipen_args import args\n"
            "or\n"
            "   >>> from pipen_args import Args\n"
            "   >>> args = Args(...)\n"
        )

    args = Args.INST

    if args.desc == ["Not described."]:
        args.desc = [pipen.desc or "Undescribed."]

    args.init(pipen)
    # NOTE: When we have [cache] defined in config file, only the same type of
    # value is accepted from command line argument `--cache`. But cache supports
    # True, False and "force". So when you need "--cache force" from command
    # line, you have to remove it from the config file if it defaults to a bool.
    args.from_arg(
        "config",
        desc="Read options from a configuration file in TOML.",
        force=True,
    )

    parsed = args.parse(args.cli_args)
    args.cli_args = None
    if parsed.profile is not None:
        pipen.profile = parsed.profile
        try:
            fileconfs = ProfileConfig.load(*CONFIG_FILES, ignore_nonexist=True)
        except KeyError:  # no default profile
            pass
        else:
            ProfileConfig.use_profile(
                fileconfs,
                pipen.profile,
            )
            config.update(fileconfs)

    if parsed.outdir is not None:
        pipen.outdir = Path(parsed.outdir).resolve()

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
        if parsed[key] is not None:
            config[key.replace("-", "_")] = parsed[key]

    if parsed["name"] not in (None, pipen.name):
        pipen.name = parsed["name"]
        pipen.workdir = Path(config["workdir"]) / slugify(pipen.name)
        pipen.workdir.mkdir(parents=True, exist_ok=True)
        if parsed["outdir"] in (None, pipen.outdir):
            pipen.outdir = Path(f"./{slugify(pipen.name)}_results").resolve()

    for key in (
        "plugin_opts",
        "template_opts",
        "scheduler_opts",
    ):
        old = copy_dict(config[key] or {}, 3)
        old.update(parsed[key] or {})
        config[key] = old

    if args.flatten_proc_args is True:
        parsed = {pipen.procs[0].name: parsed}

    for proc in pipen.procs:
        proc_args = parsed[proc.name]
        if "in" in proc_args:
            from pandas import DataFrame
            from pandas.core.dtypes.api import is_scalar

            indata = proc_args["in"]._to_dict()
            for key, val in indata.items():
                if is_scalar(val):
                    indata[key] = [val]

            maxlen = max(map(len, indata.values()))
            input_data = DataFrame(
                {
                    key: val * maxlen if len(val) == 1 and maxlen > 1 else val
                    for key, val in indata.items()
                    if val is not None and len(val) > 0
                }
            )
            # only when input data is given
            if input_data.shape[0] > 0:
                proc.input_data = input_data

        if (
            "envs" in proc_args
            and proc.envs is not None
            and proc_args["envs"] is not None
        ):
            proc.envs.update(proc_args.envs._to_dict())

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

        if "export" in proc_args:
            proc.export = proc_args["export"]

        for key in ("plugin_opts", "scheduler_opts"):
            if key in proc_args:
                if proc_args[key]:
                    proc_opts = getattr(proc, key, None)
                    if proc_opts is None:
                        setattr(proc, key, {})
                    getattr(proc, key).update(proc_args[key])


plugin.register(__name__)
