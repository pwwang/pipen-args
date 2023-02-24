import pytest

from .conftest import run_pipeline, CONFIGS_DIR


@pytest.mark.forked
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


@pytest.mark.forked
def test_process_with_config():
    out = run_pipeline(
        "process_with_config",
        gets=["Process.envs.x", "Process.envs.y"],
        args=[f"@{CONFIGS_DIR / 'process_with_config.toml'}"],
    )
    assert "Process.envs.x = 1" in out
    assert "Process.envs.y = 2" in out
