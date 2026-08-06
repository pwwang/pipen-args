"""In-process tests for the pipen-args plugin (pipen_args.plugin)

These run the plugin hooks directly in the pytest process (instead of in
subprocesses like the other tests), so that the plugin code is measured
by coverage.
"""
import asyncio
import contextlib
import sys
from types import SimpleNamespace

import pytest
from pipen import Pipen, Proc, plugin
from pipen.utils import load_pipeline
from simplug import ResultError

import pipen_args.plugin as argsplugin
from pipen_args.plugin import ArgsPlugin

from .conftest import load_in_proc, with_argv

# Parsing `--outdir`/`--workdir` emits a DeprecationWarning from argx
# (type "anypath"), which is raised as an error by the global
# `filterwarnings` config. The subprocess tests are not affected.
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture(autouse=True)
def _load_plugins():
    """Load the pipen entrypoint plugins (once per process)"""
    if "args" not in plugin.hooks._registry:
        plugin.load_entrypoints()
        # Avoid Pipen to load the entrypoints again
        Pipen.SETUP = True


class _Proc(Proc):
    """A test process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        f (flag): line1
        x (choices): line1
            - a: item a
            - b: item b
        y (type:str;hidden): line2
        z (type:int; choices:1,2,3): line3
        w (ns): line4
            - a: item a
            - b: item b
        <more>: line5
    """

    input = "a"
    output = "b:var"
    script = "echo x={{envs.x}} y={{envs.y}} > {{out.b}}"
    input_data = range(10)
    envs_depth = 2
    envs = {
        "f": True,
        "x": "a",
        "y": None,
        "z": 1,
        "w": {"a": "x", "b": 2},
    }


class _ProcBasic(Proc):
    """A basic test process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        x: x env
    """

    input = "a"
    output = "b:var"
    script = "echo {{in.a}}"
    input_data = range(10)
    envs = {"x": 1}


class _ProcTwoInputs(Proc):
    """A test process

    Input:
        a: input a
        b: input b

    Output:
        c: output c
    """

    input = "a:files, b:files"
    output = "c:file:b.txt"
    script = "echo 123 > {{out.c}}"


class _Proc2(Proc):
    """A second test process

    Input:
        a: input a
    """

    requires = _Proc
    input = "a"
    script = "echo {{in.a}}"
    plugin_opts = {"args_hide": True}


def _pipeline(**kwargs):
    return Pipen(name="test", desc="test pipeline", **kwargs)


def _basic_args(tmp_path):
    return [
        "--workdir",
        str(tmp_path / "wd"),
        "--outdir",
        str(tmp_path / "out"),
    ]


def test_on_setup_no_plugins():
    """Nothing happens without --plugins or a config file"""
    with with_argv(["pipeline.py", "--name", "test"]):
        ArgsPlugin.on_setup(SimpleNamespace(plugin_context=contextlib.nullcontext()))


def test_on_setup_plugins_with_space():
    """--plugins passed with a space is detected"""
    with with_argv(["pipeline.py", "--plugins", "-args"]):
        ArgsPlugin.on_setup(SimpleNamespace(plugin_context=contextlib.nullcontext()))
    plugin.get_plugin("args").enable()


def test_on_setup_plugins_with_eq():
    """--plugins=... passed with an equal sign is detected"""
    with with_argv(["pipeline.py", "--plugins=-args", "--name", "test"]):
        ArgsPlugin.on_setup(SimpleNamespace(plugin_context=contextlib.nullcontext()))
    plugin.get_plugin("args").enable()


def test_on_setup_plugins_in_config(tmp_path):
    """--plugins from a config file is detected"""
    config_file = tmp_path / "config.toml"
    config_file.write_text("plugins = ['-args']\n")
    with with_argv(["pipeline.py", f"@{config_file}"]):
        ArgsPlugin.on_setup(SimpleNamespace(plugin_context=contextlib.nullcontext()))
    plugin.get_plugin("args").enable()


def test_on_init_basic(tmp_path):
    """Single-proc pipeline with flattened args"""
    pipeline = _pipeline().set_start(_ProcBasic)
    pipe = load_in_proc(
        pipeline,
        _basic_args(tmp_path)
        + ["--in.a", "1", "--envs.x", "b", "--forks", "2"],
    )
    assert pipe.procs[0].envs.x == "b"
    assert pipe.procs[0].forks == 2
    # input_data is given by the process, so the cli input is ignored
    assert list(pipe.procs[0].input_data) == list(range(10))
    assert any(
        "`input_data` is given, ignore input from cli arguments" in w
        for w in argsplugin.warns
    )


def _no_data_proc():
    """A single-proc pipeline without input_data

    The process classes are created per test, since `proc.input_data`
    is set on the class by the plugin, which would leak between tests.
    """
    class _Proc(Proc):
        """A test process

        Input:
            a: input a

        Output:
            b: output b
        """

        input = "a"
        output = "b:var"
        script = "echo {{in.a}}"

    return _pipeline().set_start(_Proc)


def test_on_init_input_from_cli(tmp_path):
    """Single-proc pipeline without input_data, scalar input from cli"""
    pipe = load_in_proc(
        _no_data_proc(), _basic_args(tmp_path) + ["--in.a", "1"]
    )
    assert pipe.procs[0].input_data["a"].tolist() == ["1"]


def test_on_init_input_scalar_wrapped(tmp_path, monkeypatch):
    """A scalar input value is wrapped into a list"""
    # Input arguments are always parsed as lists, so force `is_scalar`
    # to be True to cover the wrapping branch
    import pandas.core.dtypes.api as pddapi

    monkeypatch.setattr(pddapi, "is_scalar", lambda v: True)
    pipe = load_in_proc(
        _no_data_proc(), _basic_args(tmp_path) + ["--in.a", "1"]
    )
    assert pipe.procs[0].input_data["a"].tolist() == [["1"]]


def test_on_init_input_from_cli_scalars(tmp_path):
    """Single-proc pipeline without input_data, input lists from cli"""
    pipeline = _pipeline().set_start(_ProcTwoInputs)
    pipe = load_in_proc(
        pipeline,
        _basic_args(tmp_path) + ["--in.a", "1", "--in.b", "2", "--in.b", "3"],
    )
    input_data = pipe.procs[0].input_data
    assert input_data["a"].tolist() == [["1"], ["1"]]
    assert input_data["b"].tolist() == [["2"], ["3"]]


def test_on_init_multi_proc(tmp_path):
    """Multi-proc pipeline with non-flattened args"""
    pipeline = _pipeline().set_start(_Proc)
    pipe = load_in_proc(
        pipeline,
        _basic_args(tmp_path)
        + [
            "--_Proc.forks",
            "3",
            "--_Proc.plugin_opts",
            '{"plugin_a": true}',
            "--_Proc2.plugin_opts",
            '{"plugin_b": true}',
        ],
        flatten="false",
    )
    assert pipe.procs[0].forks == 3
    assert pipe.procs[0].plugin_opts["plugin_a"] is True
    assert pipe.procs[1].plugin_opts["plugin_b"] is True


def test_on_init_plugin_opts_warns(tmp_path):
    """Warn when args_hide/args_group/args_flatten are passed by cli"""
    pipeline = _pipeline().set_start(_Proc)
    load_in_proc(
        pipeline,
        _basic_args(tmp_path)
        + [
            "--plugin_opts",
            '{"args_hide": true, "args_group": "abc", "args_flatten": false}',
        ],
        plugin_opts={"args_group": "MyGroup"},
    )
    warns = "\n".join(argsplugin.warns)
    assert "`plugin_opts.args_hide` should not be passed" in warns
    assert "`plugin_opts.args_group` should not be passed" in warns
    assert "`plugin_opts.args_flatten` should not be passed" in warns


def test_on_init_name_change(tmp_path):
    """The name is updated and used to infer the default outdir/workdir"""
    pipeline = _pipeline().set_start(_ProcBasic)
    pipe = load_in_proc(pipeline, ["--name", "other", "--forks", "1"])
    assert pipe.name == "other"
    assert str(pipe.outdir) == "other-output"
    assert str(pipe.workdir).endswith("/other")


def test_on_init_higher_priority(tmp_path):
    """Warn when outdir/workdir/forks/template_opts are given by higher priority"""
    pipeline = Pipen(
        name="test",
        desc="test pipeline",
        forks=2,
        outdir=str(tmp_path / "out_hi"),
        workdir=str(tmp_path / "wd_hi"),
        template_opts={"a": 1},
        plugin_opts={"args_dump": False},
    ).set_start(_Proc)
    pipe = load_in_proc(
        pipeline,
        [
            "--forks",
            "4",
            "--outdir",
            str(tmp_path / "out_cli"),
            "--workdir",
            str(tmp_path / "wd_cli"),
            "--template_opts",
            '{"a": 2}',
        ],
    )
    assert pipe.config.forks == 2
    assert str(pipe.outdir) == str(tmp_path / "out_hi")
    assert str(pipe.workdir) == str(tmp_path / "wd_hi" / "test")
    assert pipe.config.template_opts["a"] == 1
    warns = "\n".join(argsplugin.warns)
    assert "`forks` is given by a higher priority" in warns
    assert "`outdir` is given by a higher priority" in warns
    assert "`workdir` is given by a higher priority" in warns
    assert "`template_opts.a` is given by a higher priority" in warns


def test_on_init_profile(tmp_path, monkeypatch):
    """Load config by profile from cli"""
    config_file = tmp_path / ".pipen.toml"
    config_file.write_text("[local.scheduler_opts]\nfoo = 'bar'\n")
    monkeypatch.setattr(argsplugin, "CONFIG_FILES", (config_file,))
    pipeline = _pipeline().set_start(_Proc)
    pipe = load_in_proc(pipeline, _basic_args(tmp_path) + ["--profile", "local"])
    assert pipe.profile == "local"
    assert pipe.config.scheduler_opts.foo == "bar"


def test_on_init_profile_higher_priority(tmp_path, monkeypatch):
    """Warn when profile is given by higher priority"""
    config_file = tmp_path / ".pipen.toml"
    config_file.write_text("[local.scheduler_opts]\nfoo = 'bar'\n")
    monkeypatch.setattr(argsplugin, "CONFIG_FILES", (config_file,))
    # The profile is also loaded by pipen itself
    monkeypatch.setattr("pipen.pipen.CONFIG_FILES", (config_file,))
    pipeline = _pipeline().set_start(_Proc)
    pipeline.profile = "local"
    pipe = load_in_proc(pipeline, _basic_args(tmp_path) + ["--profile", "other"])
    assert pipe.profile == "local"
    assert any(
        "`profile` is given by a higher priority" in w for w in argsplugin.warns
    )


def test_on_init_args_dump(tmp_path):
    """Dump args to args.toml"""
    outdir = tmp_path / "out"
    pipeline = _pipeline().set_start(_Proc)
    load_in_proc(
        pipeline,
        ["--outdir", str(outdir), "--workdir", str(tmp_path / "wd")],
        plugin_opts={"args_dump": True},
    )
    assert (outdir / "args.toml").exists()
    assert any("All arguments are dumped" in i for i in argsplugin.infos)


def test_on_init_proc_group(tmp_path):
    """Single-proc pipeline with a process group"""
    from pipen_args import ProcGroup

    class PG(ProcGroup):
        """A proc group

        Args:
            x (type:int): x env
        """

        DEFAULTS = {"x": 1}

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

    pipe = load_in_proc(PG, _basic_args(tmp_path) + ["--PG.x", "3"])
    assert pipe.procs[0].envs.x == 3


def test_on_init_two_pipelines(tmp_path):
    """Using pipen-args in two pipelines at a time raises"""
    pipeline = _pipeline().set_start(_Proc)
    load_in_proc(pipeline, _basic_args(tmp_path))
    # Load a second pipeline without resetting the parser
    pipeline2 = _pipeline().set_start(_Proc)
    with pytest.raises(ResultError) as exc:
        asyncio.run(
            load_pipeline(
                pipeline2,
                argv0=sys.argv[0],
                argv1p=_basic_args(tmp_path),
                plugin_opts={"args_flatten": "auto"},
            )
        )
    assert isinstance(exc.value.__cause__, ValueError)
    assert "one pipeline at a time" in str(exc.value.__cause__)


def test_on_start(tmp_path, monkeypatch):
    """Print warnings and infos on start"""
    outdir = tmp_path / "out"
    pipeline = _pipeline().set_start(_ProcBasic)
    pipe = load_in_proc(
        pipeline,
        ["--outdir", str(outdir), "--workdir", str(tmp_path / "wd"), "--in.a", "1"],
        plugin_opts={"args_dump": True},
    )
    calls = []
    monkeypatch.setattr(argsplugin.logger, "warning", lambda msg: calls.append(msg))
    monkeypatch.setattr(argsplugin.logger, "info", lambda msg: calls.append(msg))
    asyncio.run(ArgsPlugin.on_start(pipe))
    assert any("ignore input from cli arguments" in str(c) for c in calls)
    assert any("All arguments are dumped" in str(c) for c in calls)
