from pipen import Proc, Pipen
from pipen_args import install  # noqa: F401


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        x (choices): line1
            - a: item a
            - b: item b
        y (type:str): line2
        z (atype:int; choices:1,2,3): line3
        w: line4
            - a: item a
            - b: item b
        <more>: line5
    """
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo x={{envs.x}} y={{envs.y}} > {{out.b}}'
    envs = {'x': 'a', 'y': None, "z": 1, "w": {"a": 'x', "b": 2}}


pipeline = Pipen(desc='Pipeline description.').set_start(Process)

if __name__ == '__main__':
    pipeline.run()
