from pipen import Proc, Pipen
from pipen_args import Args

args = Args(desc='Pipeline description',
            pipen_opt_group='Pipeline options')

args.add_param('o,opt', required=True, desc='A required option.')

class Process(Proc):
    """A process

    Input:
        a: Input a

    Output:
        b: Output b
    """
    input = 'a'
    input_data = range(10)
    output = 'b:var:b'
    script = 'echo {{in.a}}'

Pipen().set_starts(Process).run()
