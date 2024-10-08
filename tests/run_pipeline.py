"""Run the test pipeline with given configuration or arguments, but without
actually running the pipeline. Used for testing
"""
from __future__ import annotations
import asyncio
# import importlib
import sys
from pathlib import Path
from typing import List

from argx import ArgumentParser
from pipen import Pipen
from pipen.utils import load_pipeline

# make sure tests/pipelines can be passed as
# multiprocesses:pipeline
sys.path.insert(0, str(Path(__file__).parent / "pipelines"))


async def _run(
    pipeline: Pipen,
    args: List[str],
    gets: List[str],
    flatten: str | bool,
) -> None:
    """Run the pipeline"""
    import pipen_args
    # Inject the cli arguments to the pipeline
    pipen_args.Parser().set_cli_args(args)
    # Initialize the pipeline so that the arguments definied by
    # other plugins (i.e. pipen-args) to take in place.
    pipeline = await load_pipeline(
        pipeline,
        # disable is_loading_pipeline check
        argv0=sys.argv[0],
        argv1p=args,
        plugin_opts={"args_flatten": flatten}
    )
    # pipeline.workdir.mkdir(parents=True, exist_ok=True)
    for get in gets:
        if get == "help":
            pipen_args.Parser().print_help()
        elif get == "help+":
            pipen_args.Parser().print_help(plus=True)
        elif get in ("name", "outdir", "workdir"):
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
)

parser.add_argument(
    "++flatten",
    help="Whether to flatten the arguments, only works for single-process pipeline",
    choices=["auto", True, False],
    type=lambda x: True if x == "true" else False if x == "false" else x,
    default="auto",
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
    asyncio.run(_run(args.pipeline, args.args, args.get, args.flatten))
