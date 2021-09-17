"""Command line argument parser for pipen"""
import sys
from io import StringIO
from pathlib import Path

from pipen import plugin
from pipen.defaults import CONFIG_FILES
from pipen.utils import _logger_handler, copy_dict
from pyparam import Params
from simpleconf import Config

__version__ = "0.0.3"
__all__ = ["args"]

# pylint:disable=redefined-outer-name, unused-argument

class Args(Params):
    """Subclass of Params to fit for pipen"""

    INST = None

    def __new__(cls, *args, pipen_opt_group=None, **kwargs):
        """Singleton"""
        if cls.INST is None:
            cls.INST = super().__new__(cls)
            return cls.INST

        help_desc = kwargs.get("desc", None)
        if help_desc is not None:
            cls.INST.desc = (
                list(help_desc)
                if isinstance(help_desc, (tuple, list))
                else [help_desc]
            )
        if pipen_opt_group is not None:
            group, params = list(cls.INST.param_groups.items())[0]
            cls.INST.param_groups.pop(group)
            cls.INST.param_groups[pipen_opt_group.upper()] = params
        return cls.INST

    def __init__(self, *args, pipen_opt_group=None, **kwargs):
        """Constructor"""
        super().__init__(*args, **kwargs)
        self.pipen_opt_group = pipen_opt_group
        self.init()
        self.parsed = None
        _logger_handler.console.file = self.file = StringIO()

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
            **group_arg,
        )
        self.add_param(
            "error_strategy",
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
            **group_arg,
        )
        self.add_param(
            "num_retries",
            default=None,
            type=int,
            desc=(
                "How many times to retry the job when failed.",
                "Default: <from config>",
            ),
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
            **group_arg,
        )
        self.add_param(
            "submission_batch",
            default=None,
            type=int,
            desc=(
                "How many jobs to submit simultaneously to "
                "the scheduler system.",
                "Default: <from config>",
            ),
            **group_arg,
        )
        self.add_param(
            "workdir",
            default=None,
            type="path",
            desc=("The workdir for the pipeline.", "Default: <from config>"),
            **group_arg,
        )
        self.add_param(
            "scheduler",
            default=None,
            type=str,
            desc="The default scheduler. Default: <from config>",
            **group_arg,
        )
        self.add_param(
            "scheduler_opts",
            default=None,
            type="json",
            desc=(
                "The default scheduler options. "
                "Will update to the default one.",
                "Default: <from config>",
            ),
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
            **group_arg,
        )
        self.add_param(
            "plugin_opts",
            default=None,
            type="json",
            desc=(
                "Plugin options. Will update to the default.",
                "Default: <from config>",
            ),
            **group_arg,
        )
        self.add_param(
            "template_opts",
            default=None,
            type="json",
            desc=(
                "Template options. Will update to the default.",
                "Default: <from config>",
            ),
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


args = Args(help_on_void=False)


@plugin.impl
async def on_init(pipen):
    """Parse and update the config"""
    config = pipen.config

    if args.desc == ["Not described."]:
        args.desc = [pipen.desc]

    parsed = args.parse()
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
        "error_strategy",
        "num_retries",
        "forks",
        "submission_batch",
        "workdir",
        "scheduler",
        "plugins",
    ):
        if parsed[key] is not None:
            config[key] = parsed[key]

    for key in (
        "plugin_opts",
        "template_opts",
        "scheduler_opts",
    ):
        old = copy_dict(config[key] or {}, 3)
        old.update(parsed[key] or {})
        config[key] = old


plugin.register(__name__)
