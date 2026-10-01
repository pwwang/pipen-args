"""Regression tests for the `--out.<key>` arguments

The value given to an `--out.<key>` argument must be used when the output of
the process is computed, instead of being accepted and dropped silently.
"""
import sys
from pathlib import Path
from subprocess import run, PIPE, STDOUT

TEST_DIR = Path(__file__).parent


def run_pipeline(name: str, tmp_path: Path, args: list):
    """Run a pipeline (executing the jobs) in a subprocess"""
    pipeline_file = TEST_DIR / "pipelines" / f"{name}.py"
    return run(
        [
            sys.executable,
            str(pipeline_file),
            "--outdir",
            str(tmp_path / "out"),
            "--workdir",
            str(tmp_path / "work"),
            *args,
        ],
        stdout=PIPE,
        stderr=STDOUT,
    )


def test_out_override_value(tmp_path):
    """`--out.<key>` changes the name of the produced output file"""
    proc = run_pipeline("single_out_override", tmp_path, ["--out.b", "custom.txt"])
    stdout = proc.stdout.decode()
    assert proc.returncode == 0, stdout

    outfile = tmp_path / "out" / "Process" / "custom.txt"
    assert outfile.is_file(), stdout
    assert outfile.read_text().strip() == "x"
    # the declared name is not produced anymore
    assert not (tmp_path / "out" / "Process" / "b.txt").exists()


def test_out_override_declared_value(tmp_path):
    """Passing the declared value keeps the declared name"""
    proc = run_pipeline("single_out_override", tmp_path, ["--out.b", "b.txt"])
    stdout = proc.stdout.decode()
    assert proc.returncode == 0, stdout
    outfile = tmp_path / "out" / "Process" / "b.txt"
    assert outfile.is_file(), stdout
    assert outfile.read_text().strip() == "x"


def test_out_override_not_declared(tmp_path):
    """An `--out.<key>` that cannot be honored fails instead of being ignored"""
    proc = run_pipeline(
        "single_out_override_bad_key",
        tmp_path,
        ["--out.c", "custom.txt"],
    )
    stdout = proc.stdout.decode()
    assert proc.returncode != 0, stdout
    assert "Output key 'c' is not declared" in stdout


def test_out_override_not_flattened(tmp_path):
    """`--<Proc>.out.<key>` is honored as well (args_flatten=False)"""
    proc = run_pipeline(
        "single_out_override_not_flatten",
        tmp_path,
        ["--Process.out.b", "custom.txt"],
    )
    stdout = proc.stdout.decode()
    assert proc.returncode == 0, stdout
    outfile = tmp_path / "out" / "Process" / "custom.txt"
    assert outfile.is_file(), stdout
    assert outfile.read_text().strip() == "x"
    assert not (tmp_path / "out" / "Process" / "b.txt").exists()


def test_out_not_given(tmp_path):
    """Without `--out.<key>`, the declared output value is used"""
    proc = run_pipeline("single_out_override", tmp_path, [])
    stdout = proc.stdout.decode()
    assert proc.returncode == 0, stdout
    outfile = tmp_path / "out" / "Process" / "b.txt"
    assert outfile.is_file(), stdout
    assert not (tmp_path / "out" / "Process" / "custom.txt").exists()
