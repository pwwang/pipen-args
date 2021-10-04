"""Command line argument parser for pipen"""

import sys
from io import StringIO
from pathlib import Path

from pipen import plugin
from pipen.defaults import CONFIG_FILES
from pipen.utils import _logger_handler, copy_dict
from pyparam import Params
from simpleconf import Config

__version__ = "0.0.4"


class Args(Params):
    """Subclass of Params to fit for pipen

    Args:
        pipen_opt_group: The group name to gather all the parameters on
            help page
        hide_args: Hide some arguments in help page
    """

    INST = None

    def __new__(cls, *args, pipen_opt_group=None, hide_args=None, **kwargs):
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

    def __init__(self, *args, pipen_opt_group=None, hide_args=None, **kwargs):
        """Constructor"""
        if getattr(self, "_inited", False):
            return
        super().__init__(*args, **kwargs)
        self.pipen_opt_group = pipen_opt_group
        self.hide_args = hide_args or ()
        self.init()
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

    def init(self):
        """Define arguments"""
        group_arg = {}
        if self.pipen_opt_group is not None:
            group_arg["group"] = self.pipen_opt_group.upper()

        self.add_param(
            "profile",
            default="default",
            desc=(
                "The default profile from the configuration to run the "
                "pipeline. This profile will be used unless a profile is "
                "specified in the process or in the .run method of pipen.",
            ),
            show="profile" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "loglevel",
            default=None,
            desc=(
                "The logging level for the main logger, only takes effect "
                "after pipeline is initialized.",
                "Default: <from config>",
            ),
            show="loglevel" not in self.hide_args,
            callback=lambda val: val and val.upper(),
            **group_arg,
        )
        self.add_param(
            "cache",
            default=None,
            type=bool,
            desc=(
                "Whether enable caching for processes.",
                "Default: <from config>",
            ),
            show="cache" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "dirsig",
            default=None,
            type=int,
            desc=(
                "The depth to check the Last Modification Time of a directory.",
                "Since modifying the content won't change its LMT.",
                "Default: <from config>",
            ),
            show="dirsig" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "error-strategy",
            default=None,
            type="choice",
            choices=["ignore", "halt", "retry"],
            desc=(
                "How we should deal with job errors.",
                " - `ignore`: Let other jobs keep running. "
                "But the process is still failing when done.",
                " - `halt`: Halt the pipeline, other running jobs will be "
                "killed.",
                " - `retry`: Retry this job on the scheduler system.",
                "Default: <from config>",
            ),
            show="error_strategy" not in self.hide_args
            and "error-strategy" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "num-retries",
            default=None,
            type=int,
            desc=(
                "How many times to retry the job when failed.",
                "Default: <from config>",
            ),
            show="num_retries" not in self.hide_args
            and "num-retries" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "forks",
            default=None,
            type=int,
            desc=(
                "How many jobs to run simultaneously by the scheduler.",
                "Default: <from config>",
            ),
            show="forks" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "submission-batch",
            default=None,
            type=int,
            desc=(
                "How many jobs to submit simultaneously to "
                "the scheduler system.",
                "Default: <from config>",
            ),
            show="submission-batch" not in self.hide_args
            and "submission_batch" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "workdir",
            default=None,
            type="path",
            desc=("The workdir for the pipeline.", "Default: <from config>"),
            show="workdir" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "scheduler",
            default=None,
            type=str,
            desc="The default scheduler. Default: <from config>",
            show="scheduler" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "scheduler-opts",
            default=None,
            type="json",
            desc=(
                "The default scheduler options. "
                "Will update to the default one.",
                "Default: <from config>",
            ),
            show="scheduler_opts" not in self.hide_args
            and "scheduler-opts" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "plugins",
            type=list,
            desc=(
                "A list of plugins to only enabled or disabled for "
                "this pipeline.",
                "To disable plugins, use `no:<plugin_name>`",
                "Default: <from config>",
            ),
            show="plugins" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "plugin-opts",
            default=None,
            type="json",
            desc=(
                "Plugin options. Will update to the default.",
                "Default: <from config>",
            ),
            show="plugin_opts" not in self.hide_args
            and "plugin-opts" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "template-opts",
            default=None,
            type="json",
            desc=(
                "Template options. Will update to the default.",
                "Default: <from config>",
            ),
            show="template_opts" not in self.hide_args
            and "template-opts" not in self.hide_args,
            **group_arg,
        )
        self.add_param(
            "outdir",
            default=None,
            type="path",
            desc=(
                "The output directory for the pipeline.",
                "Default: <from config>",
            ),
            **group_arg,
        )


def __getattr__(name: str) -> Args:
    """Instantiate the instance only on import"""
    # to avoid this function to be called twice
    if name == "__path__":
        raise AttributeError
    if name == "args":
        Args.INST = Args(help_on_void=False)
        return Args.INST


@plugin.impl
async def on_init(pipen):
    """Parse and update the config"""
    if Args.INST is None:
        raise ImportError(
            "[pipen-args] Args class is not instantiated. \n"
            "Either do:\n"
            "   >>> from pipen_args import args\n"
            "or\n"
            "   >>> from pipen_args import Args\n"
            "   >>> args = Args(...)\n"
        )

    config = pipen.config

    if Args.INST.desc == ["Not described."]:
        Args.INST.desc = [pipen.desc or "Undescripbed."]

    parsed = Args.INST.parse()
    if parsed.profile is not None:
        pipen.profile = parsed.profile
        fileconfs = Config()
        fileconfs._load(*CONFIG_FILES)
        fileconfs._use(pipen.profile)
        config.update(fileconfs)

    if parsed.outdir is not None:
        pipen.outdir = Path(parsed.outdir).resolve()

    for key in (
        "loglevel",
        "cache",
        "dirsig",
        "error-strategy",
        "num-retries",
        "forks",
        "submission-batch",
        "workdir",
        "scheduler",
        "plugins",
    ):
        if parsed[key] is not None:
            config[key.replace("-", "_")] = parsed[key]

    for key in (
        "plugin-opts",
        "template-opts",
        "scheduler-opts",
    ):
        us_key = key.replace("-", "_")
        old = copy_dict(config[us_key] or {}, 3)
        old.update(parsed[key] or {})
        config[us_key] = old


plugin.register(__name__)
