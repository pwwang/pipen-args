import pytest  # noqa: F401

import sys
from pathlib import Path
from subprocess import run
from pipen import Proc
from pipen.utils import LOADING_ARGV0
from pipen_args import ProcGroup, Parser

from .conftest import fresh_parser, run_pipeline, with_argv


class PG(ProcGroup):
    """A proc group

    Args:
        x (type:int): x env
        y: y env
    """

    DEFAULTS = {"x": 1, "y": 2}

    def post_init(self) -> None:
        self.post_init_done = True

    @ProcGroup.add_proc
    def p(self):
        class Process(Proc):
            """A process

            Envs:
                x: x env
            """

            input = "a"
            input_data = range(3)
            output = "b:var:{{in.a + envs.x}}"
            script = "echo {{in.a + envs.x}}"
            envs = {"x": self.opts.x}

        return Process


def _fresh_pg():
    """Reset the singleton instance of the `PG` proc group"""
    if "_INST" in PG.__dict__:
        delattr(PG, "_INST")


def test_in_proc_parse():
    """Parse arguments in-process and load the proc group"""
    fresh_parser()
    _fresh_pg()
    with with_argv(["pipeline.py", "--PG.x", "3"]):
        pg = PG()
    assert pg.opts.x == 3
    assert pg.opts.y == 2
    assert pg.post_init_done
    assert "Process" in pg.procs
    assert pg.starts == [pg.procs["Process"]]
    assert Parser().get_action("PG.y") is not None


def test_in_proc_help():
    """Skip parsing when -h is in sys.argv"""
    fresh_parser()
    _fresh_pg()
    with with_argv(["pipeline.py", "-h"]):
        pg = PG()
    assert pg.opts.x == 1
    assert pg.post_init_done


def test_in_proc_loading():
    """Skip parsing when loading the pipeline"""
    fresh_parser()
    _fresh_pg()
    with with_argv([LOADING_ARGV0, "--PG.x", "3"]):
        pg = PG()
    assert pg.opts.x == 1


def test_in_proc_opts():
    """Update opts from the constructor arguments"""
    fresh_parser()
    _fresh_pg()
    with with_argv(["pipeline.py"]):
        pg = PG(y=5)
    assert pg.opts.y == 5


def test_integrate(tmp_path):
    out = run_pipeline(
        "proc_group_integrate",
        args=[
            "--PG.x",
            "3",
            "--workdir",
            str(tmp_path / "workdir"),
            "--outdir",
            str(tmp_path / "outdir"),
        ],
        gets=["help+"],
    )
    assert "Process Group <PG>" in out
    assert "Process <PG/Process>" in out
    assert "Process <PG/Process2>" in out

    out = run_pipeline(
        "proc_group_integrate",
        args=[
            "--PG.x",
            "3",
            "--workdir",
            str(tmp_path / "workdir"),
            "--outdir",
            str(tmp_path / "outdir"),
        ],
        gets=["Process.envs.x"],
    )
    assert "x = 3" in out


def test_as_pipen(tmp_path):
    out = run_pipeline(
        "proc_group_as_pipen",
        args=[
            "--help+",
            "--workdir",
            str(tmp_path / "workdir"),
            "--outdir",
            str(tmp_path / "outdir"),
        ],
        gets=["help+"],
    )
    # No annotation, so no help
    # assert "Process Group <PG>" in out
    assert "POST_INIT" in out
    assert "Process <PG/Process>" in out
    assert "Process <PG/Process2>" in out


def test_real_run(tmp_path):
    pipeline_file = Path(__file__).parent / "pipelines" / "proc_group_integrate.py"
    run(
        [
            sys.executable,
            pipeline_file,
            "--plugin_opts",
            '{"args_flatten": false, '
            '"args_group": "abc", '
            '"args_hide": true, '
            '"plugin_x": "y"}',
            "--forks",
            "1",
        ],
        cwd=tmp_path,
    )
    args_toml_file = tmp_path / "Pipen-output" / "args.toml"
    assert args_toml_file.exists()

    content = args_toml_file.read_text()
    assert "args_dump = true" in content
    assert "# | Arguments for process group: PG" in content
    assert "# | Arguments for process: PG/Process" in content
    assert "# | Arguments for process: PG/Process2" in content
