from pipen import Proc, Pipen


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        x (action=clear_extend;nargs=+;choices): line1
            - a: item a
            - b: item b
            - c: item c
    """
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo x={{envs.x}} y={{envs.y}} > {{out.b}}'
    envs = {'x': ['a', 'b']}


pipeline = Pipen(desc='Pipeline description.').set_start(Process)

if __name__ == '__main__':
    pipeline.run()
