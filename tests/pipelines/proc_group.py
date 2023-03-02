from pipen import Proc, Pipen, ProcGroup
import pipen_args  # noqa: F401


class PG(ProcGroup):
    """A proc group

    Args:
        x: x env
    """

    DEFAULTS = {'x': 1}

    def build(self):
        return [self.p]

    @ProcGroup.define_proc
    def p(self):
        class Process(Proc):
            """A process

            Envs:
                x: x env
            """
            input = 'a'
            input_data = range(10)
            script = 'echo {{in.a}}'
            envs = {'x': self.options.x}
        return Process

    @ProcGroup.define_proc
    def p2(self):
        class Process(Proc):
            """A process2

            Envs:
                x: x env
            """
            input = 'a'
            input_data = range(10)
            script = 'echo {{in.a}}'
        return Process


class P2(Proc):
    """A process"""
    requires = [PG().p]
    input = 'a'
    input_data = range(10)
    script = 'echo {{in.a}}'
    envs = {'x': self.options.x}