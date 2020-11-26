from pipen import Proc, Pipen
from pipen_args import Args

Args(desc='Pipeline description',
     pipen_opt_group='Pipeline options',
     help_on_void=False)

class Process(Proc):
    input_keys = 'a'
    input = range(10)
    script = 'echo {{in.a}}'

Pipen().starts(Process).run()
