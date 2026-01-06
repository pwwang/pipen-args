from pipen import Proc, Pipen


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        f (required): line1
    """
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo x={{envs.x}} y={{envs.y}} > {{out.b}}'
    # Required will be ignored since it has a default value
    envs = {'f': True}


pipeline = Pipen(
    desc='Pipeline description.',
    forks=10,
).set_start(Process)

if __name__ == '__main__':
    pipeline.run()
