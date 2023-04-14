from pipen import Proc, Pipen
from pipen_args import config


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        x: line1
        y: line2
    """
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo x={{envs.x}} y={{envs.y}} > {{out.b}}'
    # config.x is an arbitrary config item
    envs = {'x': config.x, 'y': None}


pipeline = Pipen(desc='Pipeline description.').set_start(Process)

if __name__ == '__main__':
    pipeline.run()
