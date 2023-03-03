from pipen import Proc, Pipen
from pipen_args import Parser

parser = Parser()
parser.add_argument('-x', choices=['a', 'b'], default='a')

parsed, _ = parser.parse_known_args()


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        x: line1
    """
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo x={{envs.x}} y={{envs.y}} > {{out.b}}'
    envs = {'x': parsed.x, 'y': None}


pipeline = Pipen(desc='Pipeline description.').set_start(Process)

if __name__ == '__main__':
    pipeline.run()