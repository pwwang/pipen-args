"""Command line argument parser for pipen"""
from diot import Diot

PIPEN_ARGS = Diot(
    name=Diot(
        help=(
            "The name for the pipeline, "
            "will affect the default workdir and outdir."
        )
    ),
    profile=Diot(
        help=(
            "The default profile from the configuration to run the "
            "pipeline. This profile will be used unless a profile is "
            "specified in the process or in the .run method of pipen. "
            "You can check the available profiles by running `pipen profile`"
        ),
    ),
    lang=Diot(
        help=(
            "The language interpreter to use for the pipeline/process "
            "[default: bash]"
        ),
        show=False,
    ),
    outdir=Diot(
        help="The output directory of the pipeline [default: ./<name>-output]",
        type="path",
    ),
    loglevel=Diot(
        help=(
            "The logging level for the main logger, only takes effect "
            "after pipeline is initialized [default: INFO]"
        ),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        show=False,
        type=str.upper,
    ),
    cache=Diot(
        help="\n".join(
            [
                "Whether enable caching for processes [default: True]",
                "- True: Enable caching for all processes",
                "- False: Disable caching for all processes",
                "- force: Forcing caching even when jobs signature changed",
                "   Such as envs or script file change",
            ]
        ),
        choices=[True, False, "force"],
        show=False,
        type="auto",
    ),
    dirsig=Diot(
        help=(
            "The depth to check the Last Modification Time of a directory."
            "Since modifying the content won't change its LMT."
        ),
        action="store_true",
        show=False,
    ),
    error_strategy=Diot(
        help="\n".join(
            [
                "How we should deal with job errors.",
                "- ignore: Let other jobs keep running. "
                "But the process is still failing when done.",
                "- halt: Halt the pipeline, other running jobs will be killed.",
                "- retry: Retry this job on the scheduler system.",
            ]
        ),
        choices=["ignore", "halt", "retry"],
        show=False,
    ),
    num_retries=Diot(
        help="How many times to retry the job when failed",
        type=int,
        show=False,
    ),
    forks=Diot(
        help="How many jobs to run simultaneously by the scheduler",
        type=int,
    ),
    submission_batch=Diot(
        help="How many jobs to submit simultaneously to the scheduler system",
        type=int,
        show=False,
    ),
    scheduler=Diot(help="The scheduler to run the jobs"),
    scheduler_opts=Diot(
        help="The default scheduler options. Will update to the default one",
        type="json",
        show=False,
    ),
    plugins=Diot(
        help=(
            "A list of plugins to only enabled or disabled for this pipeline. "
            "To disable plugins, use `no:<plugin_name>`"
        ),
        action="append",
        nargs="+",
        show=False,
    ),
    plugin_opts=Diot(
        help="Plugin options. Will update to the default.",
        type="json",
        show=False,
        default={},
    ),
    template_opts=Diot(
        help="Template options. Will update to the default.",
        type="json",
        show=False,
        default={},
    ),
    workdir=Diot(
        help="The working directory of the pipeline",
        show=False,
        type="path",
    ),
    order=Diot(
        help="The order of the process, larger number means later [default: 0]",
        show=False,
        default=0,
    ),
)

PIPELINE_ARGS_GROUP = "pipeline options"
FLATTEN_PROC_ARGS = "auto"
