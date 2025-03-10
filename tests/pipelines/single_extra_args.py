import sys
from pipen import Proc, Pipen
from pipen_args import parser

parser.add_extra_argument('-x', choices=['a', 'b'], default='a')
parser.add_extra_argument('-yy', type=int, required=True, fallback=1)
parsed = parser.parse_extra_args()
parsed_args = parser.parse_extra_args(args=sys.argv)
assert parsed.x == 'a'
assert parsed_args == parsed


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


pipeline = Pipen(
    desc='Pipeline description.',
    plugin_opts={"args_dump": True},
).set_start(Process)

if __name__ == '__main__':
    pipeline.run()
