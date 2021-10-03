from pipen import Proc, Pipen
from pipen_args import args

class Process(Proc):
    input = 'a'
    input_data = range(10)
    script = 'echo {{in.a}}'

Pipen(desc='Pipeline description.').set_start(Process).run()
