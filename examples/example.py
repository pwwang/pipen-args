from pipen import Proc, Pipen
from pipen_args import args

class Process(Proc):
    """My process"""
    input = 'a'
    input_data = range(10)
    script = 'echo {{in.a}}'
    plugin_opts = {"report": "a"}

Pipen(desc='Pipeline description.').set_start(Process).run()
