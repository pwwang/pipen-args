import pytest
import re
import sys
from pathlib import Path
from subprocess import check_output, run, PIPE, STDOUT
from .conftest import run_pipeline


@pytest.mark.forked
def test_name_changes_outdir():
    """Test single proc"""
    out = run_pipeline(
        "single",
        gets=["name", "outdir", "forks"],
        args=[
            "--name",
            "single",
            "--forks",
            "2",
        ],
    )
    assert "name = single" in out
    assert "forks = 2" in out
    assert re.search(r"outdir = .+/single-output", out)


@pytest.mark.forked
def test_single_proc_files():
    """Test single proc"""
    out = run_pipeline(
        "single_files",
        gets=["Process.in.a"],
        args=[
            "--in.a", "1", "2", "3",
            "--in.a", "4", "5", "6",
        ],
    )
    assert "Process.in.a = [['1', '2', '3'], ['4', '5', '6']]" in out


@pytest.mark.forked
def test_single_proc_choices():
    """Test single proc"""
    out = run_pipeline(
        "single",
        gets=["help"],
    )
    assert "--envs.x {a,b}" in out
    assert "--envs.z {1,2,3}" in out
    assert "--envs.y" not in out
    assert "--envs.w W" in out
    assert "--envs.w.a A" in out
    assert "--envs.w.b B" in out

    out = run_pipeline(
        "single",
        gets=["Process.envs.x", "Process.envs.z", "Process.envs.w.a"],
        args=[
            "--envs.x", "a",
            "--envs.z", "1",
            "--envs.w.a", "A",
        ],
    )
    assert "Process.envs.x = a" in out
    assert "Process.envs.z = 1" in out
    assert "Process.envs.w.a = A" in out


@pytest.mark.forked
def test_single_proc_list_option():
    """Test single proc"""
    out = run_pipeline(
        "single_list_option",
        gets=["Process.envs.x"],
        args=[
            "--envs.x", "b", "c"
        ],
    )
    assert "Process.envs.x = ['b', 'c']" in out


@pytest.mark.forked
def test_single_proc_with_namespace():
    """Test single proc"""
    out = run_pipeline(
        "single_list_option",
        flatten=False,
        gets=["Process.envs.x"],
        args=[
            "--Process.envs.x", "b", "c"
        ],
    )
    assert "Process.envs.x = ['b', 'c']" in out


@pytest.mark.forked
def test_single_extra_args():
    """Test single proc"""
    out = run_pipeline(
        "single_extra_args",
        gets=["Process.envs.x", "Process.envs.y"],
        args=[
            "-x", "a",
            "--envs.y", "b",
        ],
    )
    assert "Process.envs.x = a" in out
    assert "Process.envs.y = b" in out


@pytest.mark.forked
def test_single_extra_args_help():
    """Test single proc with --help"""
    pipeline_file = Path(__file__).parent / "pipelines" / "single_extra_args.py"
    out = check_output([sys.executable, str(pipeline_file), "--help+"])
    out = run_pipeline("single_extra_args", gets=["help"])
    assert "-x" in out
    assert "--envs.x" in out
    assert "--out.b" in out


@pytest.mark.forked
def test_warns_when_data_is_set():
    """Test single proc"""
    out = run_pipeline(
        "single",
        gets=["Process.in"],
        args=["--in", "a"],
    )
    assert "Process.in = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]" in out


@pytest.mark.forked
def test_scalar_input(tmp_path):
    """Test single proc"""
    configfile = tmp_path / "config.toml"
    configfile.write_text("[in]\na = 'b'\n")
    run_pipeline(
        "single_files",
        gets=["Process.in"],
        args=[f"@{configfile}", "--workdir", str(tmp_path / "workdir")],
    )


@pytest.mark.forked
def test_outdir_workdir_using_name(tmp_path):
    """Test single proc"""
    out = run_pipeline(
        "single",
        gets=["workdir", "outdir"],
        args=["--name", "xyz"],
    )
    assert ".pipen/xyz" in out
    assert "xyz-output" in out


@pytest.mark.forked
def test_outdir(tmp_path):
    """Test single proc"""
    out = run_pipeline(
        "single",
        gets=["outdir"],
        args=["--outdir", "xyz"],
    )
    assert "xyz" in out


@pytest.mark.forked
def test_outdir_workdir(tmp_path):
    """Test single proc"""
    out = run_pipeline(
        "single_outdir_workdir",
        gets=["outdir", "workdir"],
        args=["--outdir", "abcd", "--workdir", "defg"],
    )
    assert "outdir = /tmp/single_outdir_workdir_outdir" in out
    assert "workdir = /tmp/single_outdir_workdir_workdir/Pipen" in out


@pytest.mark.forked
def test_used_in_two_pipelines():
    """Test single proc"""
    plfile = Path(__file__).parent / "pipelines" / "two_pipelines.py"
    p = run([sys.executable, str(plfile)], stderr=STDOUT, stdout=PIPE)
    assert p.returncode == 1
    assert "can only be used in one pipeline at a time" in p.stdout.decode()


@pytest.mark.forked
def test_required_with_default():
    """Test single proc"""
    plfile = (
        Path(__file__).parent / "pipelines" / "single_required_with_default.py"
    )
    p = run([sys.executable, str(plfile)], stderr=STDOUT, stdout=PIPE)
    # Should succeed
    assert p.returncode == 0
