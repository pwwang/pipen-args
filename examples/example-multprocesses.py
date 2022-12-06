from pipen import Proc, Pipen
from pipen_args import args  # noqa: F401


class Process1(Proc):
    """Process 1

    Output:
        b: output b

    Envs:
        x: line1
            line2
            >>> code
    """

    input = "a"
    input_data = range(10)
    output = "b:var"
    lang = "bash"
    envs = {"x": 1}
    script = "echo {{in.a}}"


class Process2(Proc):
    """Process 2"""

    requires = Process1
    input = "a"
    script = "echo {{in.a}}"
    plugin_opts = {"args_hide": True}


Pipen(
    desc="Pipeline description.",
    plugins=["no:report"],
).set_start(Process1).run()
