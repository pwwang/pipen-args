from pipen import Proc, Pipen
from pipen_args import Args

Args(
    desc="Pipeline description",
    hidden_args=[
        "scheduler_opts",
        "plugin_opts",
        "template_opts",
        "dirsig",
        "loglevel",
        "plugins",
        "submission_batch",
    ],
    help_on_void=False,
)


class Process(Proc):
    input = "a"
    # input_data = range(10)
    script = "echo {{in.a}}"


Pipen().set_starts(Process).run()
