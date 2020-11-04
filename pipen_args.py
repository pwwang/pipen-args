"""Command line argument parser for pipen"""
from pyparam import Params
from pipen.plugin import plugin
from pipen.utils import logger

__version__ = '0.0.0'
__all__ = ['params']

name = 'args'

params = Params(help_on_void=False)

@plugin.impl
def on_init(pipen):
    """Setup and parse the arguments when the pipeline is initialized."""
    config = pipen.config
    params.add_param(
        'profile',
        default='default',
        desc=('The default profile from the configuration to run the pipeline.',
              'This profile will be used unless a profile is specified in the '
              'process or in the .run method of pipen.')
    )
    params.add_param(
        'loglevel',
        default=config.loglevel,
        desc=('The logging level for the main logger, only takes effect '
              'after pipeline is initialized.'),
        callback=lambda val: val and val.upper()
    )
    params.add_param(
        'cache',
        default=config.cache,
        type=bool,
        desc=('Whether enable caching for processes.')
    )
    params.add_param(
        'dirsig',
        default=config.dirsig,
        type=int,
        desc=('The depth to check the Last Modification Time of a directory.',
              'Since modify the content of a directory won\'t change its LMT.')
    )
    params.add_param(
        'error_strategy',
        default=config.error_strategy,
        type='choice',
        choices=['ignore', 'halt', 'retry'],
        desc=('How we should deal with job errors.',
              ' - `ignore`: Let other jobs keep running. '
              'But the process is still failing when done.',
              ' - `halt`: Halt the pipeline, other running jobs will be '
              'killed.',
              ' - `retry`: Retry this job on the scheduler system.')
    )
    params.add_param(
        'num_retries',
        default=config.num_retries,
        type=int,
        desc='How many times to retry the job when failed.'
    )
    params.add_param(
        'forks',
        default=config.forks,
        type=int,
        desc='How many jobs to run simultaneously on the scheduler system.'
    )
    params.add_param(
        'submission_batch',
        default=config.submission_batch,
        type=int,
        desc='How many jobs to submit simultaneously to the scheduler system.'
    )
    params.add_param(
        'workdir',
        default=config.workdir,
        type='path',
        desc='The workdir for the pipeline.'
    )
    params.add_param(
        'envs',
        default=config.envs,
        type='json',
        desc=('The env variables for template rendering. ',
              'Will update to the default one.')
    )
    params.add_param(
        'scheduler',
        default=config.scheduler,
        type=str,
        desc='The default scheduler'
    )
    params.add_param(
        'scheduler_opts',
        default=config.scheduler_opts,
        type='json',
        desc='The default scheduler options. Will update to the default one.'
    )
    params.add_param(
        'plugins',
        default=config.plugins,
        type=list,
        desc=(
            'A list of plugins to only enabled or disabled for this pipeline.',
            'To disable plugins, use `no:<plugin_name>`'
        )
    )
    params.add_param(
        'plugin_opts',
        default=config.plugin_opts,
        type='json',
        desc='Plugin options. Will update to the default one.'
    )
    params.add_param(
        'outdir',
        default=pipen.outdir,
        type='path',
        desc='The output directory for the pipeline.'
    )

    params.desc = [pipen.desc]
    parsed = params.parse()
    pipen.profile = parsed.profile
    pipen.outdir = parsed.outdir
    if parsed.loglevel != config.loglevel:
        logger.setLevel(parsed.loglevel)

    args = {'default': {}}
    if parsed.cache != config.cache:
        args['default']['cache'] = parsed.cache
    if parsed.dirsig != config.dirsig:
        args['default']['dirsig'] = parsed.dirsig
    if parsed.error_strategy != config.error_strategy:
        args['default']['error_strategy'] = parsed.error_strategy
    if parsed.num_retries != config.num_retries:
        args['default']['num_retries'] = parsed.num_retries
    if parsed.forks != config.forks:
        args['default']['forks'] = parsed.forks
    if parsed.submission_batch != config.submission_batch:
        args['default']['submission_batch'] = parsed.submission_batch
    if parsed.workdir != config.workdir:
        args['default']['workdir'] = parsed.workdir
    if parsed.envs != config.envs:
        envs = config.envs.copy()
        envs.update(parsed.envs)
        args['default']['envs'] = envs
    if parsed.scheduler != config.scheduler:
        args['default']['scheduler'] = parsed.scheduler
    if parsed.scheduler_opts != config.scheduler_opts:
        scheduler_opts = config.scheduler_opts.copy()
        scheduler_opts.update(parsed.scheduler_opts)
        args['default']['scheduler_opts'] = scheduler_opts
    if parsed.plugins != config.plugins:
        args['default']['plugins'] = parsed.plugins
    if parsed.plugin_opts != config.plugin_opts:
        plugin_opts = config.plugin_opts.copy()
        plugin_opts.update(parsed.plugin_opts)
        args['default']['plugin_opts'] = plugin_opts

    pipen.config._load(args)

plugin.register(__name__)
