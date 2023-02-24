from pipen import Proc, Pipen
import pipen_args  # noqa: F401


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b
    """
    input = 'a:files'
    output = 'b:file:b.txt'
    script = 'echo 123 > {{out.b}}'


pipeline = Pipen(desc='Pipeline description.').set_start(Process)

if __name__ == '__main__':
    pipeline.run()
