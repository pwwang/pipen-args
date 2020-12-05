"""Command line argument parser for pipen"""
import sys
from io import StringIO
from pyparam import Params
from pipen.plugin import plugin
from pipen.utils import logger, _logger_handler

__version__ = '0.0.2'
__all__ = ['args']

class Args(Params):

    INST = None

    def __new__(cls, pipen_opt_group=None, *args, **kwargs):
        if cls.INST is None:
            cls.INST = super().__new__(cls)
            return cls.INST

        help_desc = kwargs.get('desc', None)
        if help_desc is not None:
            cls.INST.desc = (list(help_desc)
                             if isinstance(help_desc, (tuple, list))
                             else [help_desc])
        if pipen_opt_group is not None:
            group, params = list(cls.INST.param_groups.items())[0]
            cls.INST.param_groups.pop(group)
            cls.INST.param_groups[pipen_opt_group.upper()] = params
        return cls.INST

    def __init__(self, pipen_opt_group=None, *args, **kwargs):
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
        group_arg = {}
        if self.pipen_opt_group is not None:
            group_arg['group'] = self.pipen_opt_group.upper()
        self.add_param(
            'profile',
            default='default',
            desc=(
                'The default profile from the configuration to run the ',
                'pipeline. This profile will be used unless a profile is '
                'specified in the process or in the .run method of pipen.'
            ),
            **group_arg
        )
        self.add_param(
            'loglevel',
            default=None,
            desc=('The logging level for the main logger, only takes effect '
                  'after pipeline is initialized.',
                  'Default: <from config>'),
            callback=lambda val: val and val.upper(),
            **group_arg
        )
        self.add_param(
            'cache',
            default=None,
            type=bool,
            desc=('Whether enable caching for processes.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'dirsig',
            default=None,
            type=int,
            desc=(
                'The depth to check the Last Modification Time of a directory.',
                'Since modifying the content won\'t change its LMT.',
                'Default: <from config>'
            ),
            **group_arg
        )
        self.add_param(
            'error_strategy',
            default=None,
            type='choice',
            choices=['ignore', 'halt', 'retry'],
            desc=('How we should deal with job errors.',
                ' - `ignore`: Let other jobs keep running. '
                'But the process is still failing when done.',
                ' - `halt`: Halt the pipeline, other running jobs will be '
                'killed.',
                ' - `retry`: Retry this job on the scheduler system.',
                'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'num_retries',
            default=None,
            type=int,
            desc=('How many times to retry the job when failed.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'forks',
            default=None,
            type=int,
            desc=('How many jobs to run simultaneously by the scheduler.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'submission_batch',
            default=None,
            type=int,
            desc=('How many jobs to submit simultaneously to '
                  'the scheduler system.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'workdir',
            default=None,
            type='path',
            desc=('The workdir for the pipeline.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'envs',
            default=None,
            type='json',
            desc=('The env variables for template rendering. ',
                  'Will update to the default one.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'scheduler',
            default=None,
            type=str,
            desc='The default scheduler. Default: <from config>',
            **group_arg
        )
        self.add_param(
            'scheduler_opts',
            default=None,
            type='json',
            desc=('The default scheduler options. '
                  'Will update to the default one.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'plugins',
            type=list,
            desc=(
                'A list of plugins to only enabled or disabled for '
                'this pipeline.',
                'To disable plugins, use `no:<plugin_name>`',
                'Default: <from config>'
            ),
            **group_arg
        )
        self.add_param(
            'plugin_opts',
            default=None,
            type='json',
            desc=('Plugin options. Will update to the default one.',
                  'Default: <from config>'),
            **group_arg
        )
        self.add_param(
            'outdir',
            default=None,
            type='path',
            desc=('The output directory for the pipeline.',
                  'Default: <from config>'),
            **group_arg
        )

args = Args(help_on_void=False)

@plugin.impl
def on_init(pipen):
    """Parse and update the config"""
    config = pipen.config

    if args.desc == ['Not described.']:
        args.desc = [pipen.desc]

    parsed = args.parse()
    if parsed.profile is not None:
        pipen.profile = parsed.profile
    if parsed.outdir is not None:
        pipen.outdir = parsed.outdir
    if parsed.loglevel is not None:
        logger.setLevel(parsed.loglevel)

    config_args = {'default': {}}
    if parsed.cache is not None:
        config_args['default']['cache'] = parsed.cache
    if parsed.dirsig is not None:
        config_args['default']['dirsig'] = parsed.dirsig
    if parsed.error_strategy is not None:
        config_args['default']['error_strategy'] = parsed.error_strategy
    if parsed.num_retries is not None:
        config_args['default']['num_retries'] = parsed.num_retries
    if parsed.forks is not None:
        config_args['default']['forks'] = parsed.forks
    if parsed.submission_batch is not None:
        config_args['default']['submission_batch'] = parsed.submission_batch
    if parsed.workdir is not None:
        config_args['default']['workdir'] = parsed.workdir
    if parsed.envs is not None:
        envs = config.envs.copy()
        envs.update(parsed.envs)
        config_args['default']['envs'] = envs
    if parsed.scheduler is not None:
        config_args['default']['scheduler'] = parsed.scheduler
    if parsed.scheduler_opts is not None:
        scheduler_opts = config.scheduler_opts.copy()
        scheduler_opts.update(parsed.scheduler_opts)
        config_args['default']['scheduler_opts'] = scheduler_opts
    if not parsed.plugins:
        config_args['default']['plugins'] = parsed.plugins
    if parsed.plugin_opts is not None:
        plugin_opts = config.plugin_opts.copy()
        plugin_opts.update(parsed.plugin_opts)
        config_args['default']['plugin_opts'] = plugin_opts

    pipen.config._load(config_args)

plugin.register(__name__)
