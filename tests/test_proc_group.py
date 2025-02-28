import pytest

import sys
from pathlib import Path
from subprocess import run
from .conftest import run_pipeline


@pytest.mark.forked
def test_integrate():
    out = run_pipeline(
        "proc_group_integrate",
        args=["--PG.x", "3"],
        gets=["help+"],
    )
    assert "Process Group <PG>" in out
    assert "Process <PG/Process>" in out
    assert "Process <PG/Process2>" in out

    out = run_pipeline(
        "proc_group_integrate",
        args=["--PG.x", "3"],
        gets=["Process.envs.x"],
    )
    assert "x = 3" in out


@pytest.mark.forked
def test_as_pipen():
    out = run_pipeline(
        "proc_group_as_pipen",
        args=["--help+"],
        gets=["help+"],
    )
    # No annotation, so no help
    # assert "Process Group <PG>" in out
    assert "POST_INIT" in out
    assert "Process <PG/Process>" in out
    assert "Process <PG/Process2>" in out


@pytest.mark.forked
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
