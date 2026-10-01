from pipen import Proc, Pipen


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b
    """

    input = "a"
    output = "b:file:b.txt"
    input_data = ["x"]
    script = "echo {{in.a}} > {{out.b}}"


pipeline = Pipen(
    desc="Pipeline for testing the `--<Proc>.out.<key>` override (not flattened).",
    plugin_opts={"args_flatten": False},
).set_start(Process)

if __name__ == "__main__":
    pipeline.run()
