from pipen import Proc, Pipen


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        f (flag): line1
        x (choices): line1
            - a: item a
            - b: item b
        y (type:str;hidden): line2
        z (type:int; choices:1,2,3): line3
        w (ns): line4
            - a: item a
            - b: item b
        t (type=json): line4, a json object
        <more>: line5
    """

    input = "a"
    output = "b:file:b.txt"
    input_data = range(10)
    envs_depth = 2
    script = "echo x={{envs.x}} y={{envs.y}} > {{out.b}}"
    envs = {
        "f": True,
        "x": "a",
        "y": None,
        "z": 1,
        "w": {"a": "x", "b": 2},
        "t": {"a": 1, "b": 2},
    }


pipeline = Pipen(
    desc="Pipeline description.",
    plugin_opts={"args_dump": True},
).set_start(Process)

if __name__ == "__main__":
    pipeline.run()
