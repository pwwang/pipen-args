import pytest  # noqa: F401

from .conftest import run_pipeline


def test_multi_proc():
    """Test multi proc"""
    out = run_pipeline(
        "multiprocesses",
        gets=["Process1.envs.x", "Process2.forks"],
        args=["--Process1.envs.x", "3", "--Process2.forks", "4"],
    )
    assert "Process1.envs.x = 3" in out
    assert "Process2.forks = 4" in out


def test_multi_proc_help():
    """Test multi proc"""
    out = run_pipeline("multiprocesses", gets=["help"])
    assert "--name NAME" in out
    assert "--cache" not in out

    out = run_pipeline("multiprocesses", gets=["help+"])
    assert "--cache {True,False,force}" in out


def test_multi_proc_plugin_opts():
    out = run_pipeline(
        "multiprocesses",
        args=["--Process2.plugin_opts", '{"plugin_a": true}'],
        gets=["Process2.plugin_opts.plugin_a"],
    )
    assert "Process2.plugin_opts.plugin_a = True" in out


def test_multi_proc_args_hide():
    """Test multi proc"""
    out = run_pipeline(
        "multiprocesses_args_hide",
        gets=["help"],
    )
    assert "Process2" not in out

    out = run_pipeline(
        "multiprocesses_args_hide",
        gets=["help+"],
    )
    assert "Process2" in out
