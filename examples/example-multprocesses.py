from pipen import Proc, Pipen
from pipen_args import args

class Process1(Proc):
    """Process 1

    Output:
        b: output b
    """
    input = 'a'
    input_data = range(10)
    output = 'b:var'
    envs = {"x": 1}
    script = 'echo {{in.a}}'

class Process2(Proc):
    """Process 2
    """
    requires = Process1
    input = 'a'
    script = 'echo {{in.a}}'

Pipen(desc='Pipeline description.').set_start(Process1).run()
