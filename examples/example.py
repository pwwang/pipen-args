from pipen import Proc, Pipen
from pipen_args import args  # noqa: F401


class Process(Proc):
    """My process"""
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo {{in.a}} > {{out.b}}'
    plugin_opts = {"report": "a"}


(
    Pipen(desc='Pipeline description.', plugins=["no:report"])
    .set_start(Process)
    .run()
)
