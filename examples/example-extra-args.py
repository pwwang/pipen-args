from pipen import Proc, Pipen
from pipen_args import Args

args = Args(desc='Pipeline description',
            pipen_opt_group='Pipeline options')

args.add_param('o,opt', required=True, desc='A required option.')
args = args.parse()

class Process(Proc):
    input_keys = 'a'
    input = range(10)
    script = 'echo {{in.a}}'

Pipen().set_starts(Process).run()
