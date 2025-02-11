import os

os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs"))

from pipen import Proc, Pipen  # noqa: E402


class Process(Proc):
    """My process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        j (type=json): JSON option
        f (flag): line1
        x (choices): line1
            - a: item a
            - b: item b
        y (type:str;hidden): line2
        z (type:int; choices:1,2,3): line3
        w (ns): line4
            - a: item a
            - b: item b
        <more>: line5
    """

    input = "a"
    output = "b:file:b.txt"
    input_data = range(10)
    script = "echo x={{envs.x}} y={{envs.y}} > {{out.b}}"
    envs = {
        "j": {"a": 1, "b": 2, "c": [1, 2, 3], "d.d": {"e": 4, "f": 5}},
        "f": True,
        "x": "a",
        "y": None,
        "z": 1,
        "w": {"a": "x", "b": 2},
    }


pipeline = Pipen(
    desc="Pipeline description.",
    plugin_opts={"args_dump": True},
).set_start(Process)
pipeline.profile = "test_sched"

if __name__ == "__main__":
    pipeline.run("test_sched")
