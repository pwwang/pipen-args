import pytest

from .conftest import run_pipeline


@pytest.mark.forked
def test_multi_proc():
    """Test multi proc"""
    out = run_pipeline("multiprocesses")
    assert "# procs          = 2" in out
    assert "Process1: <<< [START]" in out
    assert "Process2: >>> [END]" in out


def test_multi_proc_help():
    """Test multi proc"""
    out = run_pipeline("multiprocesses", ["--help"])
    assert "--name NAME" in out
    assert "--cache" not in out

    out = run_pipeline("multiprocesses", ["--help+"])
    assert "--cache {True,False,force}" in out
