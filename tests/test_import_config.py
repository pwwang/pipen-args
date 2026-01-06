import pytest  # noqa: F401

import contextlib
from .conftest import run_pipeline, CONFIGS_DIR


@contextlib.contextmanager
def with_argv(new_argv):
    import sys
    original_argv = sys.argv.copy()

    sys.argv = new_argv
    yield
    sys.argv = original_argv


def test_bare_config():
    out = run_pipeline(
        "bare_config",
        gets=["a"],
        args=[f"@{CONFIGS_DIR / 'bare.toml'}"],
    )
    assert out.strip() == "a = 1"

    out = run_pipeline(
        "bare_config",
        gets=["a"],
    )
    assert out.strip() == "a = 10"


def test_process_with_config():
    out = run_pipeline(
        "process_with_config",
        gets=["Process.envs.x", "Process.envs.y"],
        args=[f"@{CONFIGS_DIR / 'process_with_config.toml'}"],
    )
    assert "Process.envs.x = 1" in out
    assert "Process.envs.y = 2" in out


def test_import_config_file():
    with with_argv(
        [
            "pipeline.py",
            f"@{CONFIGS_DIR / 'import_config_file.toml'}",
        ]
    ):
        from pipen_args import config_file
        assert config_file == str(CONFIGS_DIR / "import_config_file.toml")

    with with_argv(
        [
            "pipeline.py",
        ]
    ):
        from pipen_args import config_file
        assert config_file is None
