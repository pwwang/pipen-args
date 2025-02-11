from pipen import Proc
from pipen_args import ProcGroup


class PG(ProcGroup):
    """A proc group
    """

    DEFAULTS = {'x': 1}

    def post_init(self) -> None:
        print("POST_INIT")

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


pipeline = PG().as_pipen(plugin_opts={"args_dump": True})

if __name__ == '__main__':
    pipeline.run()
