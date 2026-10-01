from pipen import Proc, Pipen


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b
        c: output c, which is not declared in the output of the process
    """

    input = "a"
    output = "b:file:b.txt"
    input_data = ["x"]
    script = "echo {{in.a}} > {{out.b}}"


pipeline = Pipen(
    desc="Pipeline for testing that an unhonored `--out.<key>` fails."
).set_start(Process)

if __name__ == "__main__":
    pipeline.run()
