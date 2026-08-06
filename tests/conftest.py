import asyncio
import sys
from contextlib import contextmanager
from subprocess import check_output
from panpath import PanPath
from typing import List, Union

TEST_DIR = PanPath(__file__).parent.resolve()
CONFIGS_DIR = TEST_DIR / "configs"


def fresh_parser():
    """Reset the singleton `Parser` and return a new instance"""
    from pipen_args.parser_ import Parser

    if "_INST" in Parser.__dict__:
        delattr(Parser, "_INST")
    return Parser()


def load_in_proc(pipeline, args, flatten="auto", **kwargs):
    """Load a pipeline in-process (no subprocess) with the given `args`

    Mirror of `run_pipeline`, but without spawning a subprocess, so that
    the code is measured by coverage.
    """
    from pipen.utils import load_pipeline

    fresh_parser().set_cli_args(args)
    kwargs.setdefault("plugin_opts", {}).update({"args_flatten": flatten})
    return asyncio.run(
        load_pipeline(
            pipeline,
            argv0=sys.argv[0],
            argv1p=args,
            **kwargs,
        )
    )


def run_pipeline(
    pipeline: str,
    gets: List[str],
    args: List[str] = [],
    flatten: Union[str, bool] = "auto",
) -> str:
    """Run a pipeline with `args`"""
    cmd = [
        sys.executable,
        str(TEST_DIR / "run_pipeline.py"),
        f"{pipeline}:pipeline",
        "++flatten",
        str(flatten).lower(),
        "++args",
        *args,
        "++gets",
        *gets,
    ]
    try:
        return check_output(cmd, encoding="utf-8")
    except Exception as e:
        return f"Error: {e}\n\nCommand:\n  " + " ".join(cmd)


@contextmanager
def with_argv(argv: List[str]):
    """Set sys.argv temporarily"""
    old_argv = sys.argv
    sys.argv = argv
    yield
    sys.argv = old_argv
