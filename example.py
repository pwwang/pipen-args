from pipen import Proc, Pipen
from pipen_args import params

class Process(Proc):
    input_keys = 'a'
    input = range(10)
    script = 'echo {{in.a}}'

Pipen(starts=Process).run()
