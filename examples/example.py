from pipen import Proc, Pipen
import pipen_args

class Process(Proc):
    input_keys = 'a'
    input = range(10)
    script = 'echo {{in.a}}'

Pipen(desc='Pipeline description.').starts(Process).run()
