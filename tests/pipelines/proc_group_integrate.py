from pipen import Proc, Pipen
from pipen_args import ProcGroup, install  # noqa: F401


class PG(ProcGroup):
    """A proc group

    Args:
        x (type:int): x env
    """

    DEFAULTS = {'x': 1}

    @ProcGroup.add_proc
    def p(self):
        class Process(Proc):
            """A process

            Envs:
                x: x env
            """
            input = 'a'
            input_data = range(3)
            output = 'b:var:{{in.a + envs.x}}'
            script = 'echo {{in.a + envs.x}}'
            envs = {'x': self.opts.x}
        return Process

    @ProcGroup.add_proc
    def p2(self):
        class Process2(Proc):
            """A process2
            """
            requires = self.p
            input = 'a'
            output = 'b:var:{{in.a * 2}}'
            script = 'echo {{in.a}}'
        return Process2


class P2(Proc):
    """A process3"""
    requires = [PG().p2]
    input = 'a'
    output = 'b:file:b.txt'
    script = 'echo {{in.a}} > {{out.b}}'


pipeline = Pipen(desc='Pipeline description.').set_start(PG().starts)

if __name__ == '__main__':
    pipeline.run()
