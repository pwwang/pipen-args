from pipen import Proc, Pipen
from pipen_args import args, config  # noqa: F401

# Get the config from "--config" file even before parsed
print(config)


class Process(Proc):
    """My process"""
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo {{in.a}} > {{out.b}}'
    plugin_opts = {"report": "a"}


Pipen(desc='Pipeline description.').set_start(Process).run()
