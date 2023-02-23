import sys
from subprocess import check_output
from pathlib import Path
from typing import List

PIPELINE_DIR = Path(__file__).parent.resolve() / "pipelines"


def run_pipeline(pipeline: str, args: List[str] = []) -> str:
    """Run a pipeline with `args`"""
    try:
        return check_output(
            [sys.executable, PIPELINE_DIR / f"{pipeline}.py", *args],
            encoding="utf-8",
        )
    except Exception as e:
        return str(e)
