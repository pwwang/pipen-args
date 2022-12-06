from pipen import Proc, Pipen
from pipen_args import Args

Args(desc='Pipeline description',
     pipen_opt_group='A lot of pipeline options',
     help_on_void=False)


class Process(Proc):
    input = 'a'
    # input_data = range(10)
    script = 'echo {{in.a}}'


Pipen().set_start(Process).run()
