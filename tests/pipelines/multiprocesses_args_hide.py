from pipen import Proc, Pipen


class Process1(Proc):
    """Process 1

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        x: line1
    """

    input = "a"
    input_data = range(10)
    output = "b:var"
    lang = "bash"
    envs = {"x": 1}
    script = "echo {{in.a}}"


class Process2(Proc):
    """Process 2

    Input:
        a: input a
    """

    requires = Process1
    input = "a"
    script = "echo {{in.a}}"
    plugin_opts = {"args_hide": True}


pipeline = Pipen(
    desc="Pipeline description.",
    plugins=["-report"],
).set_start(Process1)

if __name__ == "__main__":
    pipeline.run()
