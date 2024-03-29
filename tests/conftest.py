import sys
from subprocess import check_output
from pathlib import Path
from typing import List, Union

TEST_DIR = Path(__file__).parent.resolve()
CONFIGS_DIR = TEST_DIR / "configs"


def run_pipeline(
    pipeline: str,
    gets: List[str],
    args: List[str] = [],
    flatten: Union[str, bool] = "auto",
) -> str:
    """Run a pipeline with `args`"""
    try:
        return check_output(
            [
                sys.executable,
                str(TEST_DIR / "run_pipeline.py"),
                f"{pipeline}:pipeline",
                "++flatten",
                str(flatten).lower(),
                "++args",
                *args,
                "++gets",
                *gets,
            ],
            encoding="utf-8",
        )
    except Exception as e:
        return str(e)
