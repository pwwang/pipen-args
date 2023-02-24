"""Run the test pipeline with given configuration or arguments, but without
actually running the pipeline. Used for testing
"""
from __future__ import annotations
import asyncio
import importlib
import sys
from pathlib import Path
from typing import List

from argx import ArgumentParser
from pipen import Pipen

# make sure tests/pipelines can be passed as
# multiprocesses:pipeline
sys.path.insert(0, str(Path(__file__).parent / "pipelines"))


def _parse_pipeline(pipeline: str) -> Pipen:
    """Parse the pipeline"""
    modpath, sep, name = pipeline.rpartition(":")
    if sep != ":":
        raise ValueError(
            f"Invalid pipeline: {pipeline}.\n"
            "It must be in the format '<module[.submodule]>:pipeline' or \n"
            "'/path/to/pipeline.py:pipeline'"
        )

    path = Path(modpath)
    if path.is_file():
        spec = importlib.util.spec_from_file_location(path.stem, modpath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(modpath)

    try:
        pipeline = getattr(module, name)
    except AttributeError:
        raise ValueError(f"Invalid pipeline: {pipeline}") from None

    if callable(pipeline):
        pipeline = pipeline()

    if not isinstance(pipeline, Pipen):
        raise ValueError(
            f"Invalid pipeline: {pipeline}\n"
            "It must be a `pipen.Pipen` instance"
        )

    return pipeline


async def _run(pipeline: Pipen, args: List[str], gets: List[str]) -> None:
    """Run the pipeline"""
    import pipen_args
    # Inject the cli arguments to the pipeline
    sys.argv = [pipeline.name] + args
    # Initialize the pipeline so that the arguments definied by
    # other plugins (i.e. pipen-args) to take in place.
    await pipeline._init()
    for get in gets:
        if get == "help":
            pipen_args.Parser.INST.print_help()
        elif get == "help+":
            pipen_args.Parser.INST.print_help(plus=True)
        elif get in ("name", "outdir"):
            print(f"{get} = {getattr(pipeline, get)}")
        elif get in pipeline.config:
            print(f"{get} = {pipeline.config[get]}")
        elif "." in get:
            procname, *keys = get.split(".")
            for proc in pipeline.procs:
                if proc.name == procname:
                    break
            else:
                raise ValueError(f"No such process: {procname}")

            if keys[0] == "in":
                keys[0] = "input_data"

            val = getattr(proc, keys[0])
            for key in keys[1:]:
                val = val[key]

            if keys[0] == "input_data":
                val = list(val)
            print(f"{get} = {val}")
        else:
            raise ValueError(f"Invalid get: {get}")


parser = ArgumentParser(
    description="Run the test pipeline with given configuration or arguments, "
    "but without actually running the pipeline. Used for testing",
    prefix_chars="+",
)

parser.add_argument(
    "pipeline",
    help="The pipeline to run, either `<pipeline.py>:<pipeline>` or "
    "`<module.submodule>:<pipeline>`",
    type=_parse_pipeline,
)

parser.add_argument(
    "++args",
    help="The arguments to run the pipeline",
    nargs="*",
    default=[],
    action="extend",
)

parser.add_argument(
    "++get",
    "++gets",
    help="Get the value of the given configuration",
    action="extend",
    nargs="+",
    default=[],
)


if __name__ == "__main__":
    args = parser.parse_args()
    asyncio.run(_run(args.pipeline, args.args, args.get))
