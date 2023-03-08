import pytest

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
