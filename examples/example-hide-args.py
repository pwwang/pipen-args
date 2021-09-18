from pipen import Proc, Pipen
from pipen_args import Args

Args(
    desc="Pipeline description",
    hide_args=[
        "scheduler-opts",
        "plugin-opts",
        "template-opts",
        "dirsig",
        "loglevel",
        "plugins",
        "submission-batch",
    ],
    help_on_void=False,
)


class Process(Proc):
    input = "a"
    # input_data = range(10)
    script = "echo {{in.a}}"


Pipen().run(Process)
