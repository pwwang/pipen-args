from pipen import Proc, Pipen
import pipen_args

class Process(Proc):
    input = 'a'
    input_data = range(10)
    script = 'echo {{in.a}}'

Pipen(desc='Pipeline description.').run(Process)
