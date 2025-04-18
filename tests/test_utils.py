import pytest  # noqa: F401
from unittest.mock import MagicMock
from argx.action import NamespaceAction, HelpAction
from argx.parser import ArgumentParser, _NamespaceArgumentGroup
from pipen_args.utils import (
    _sort_dict,
    _dump_dict,
    dump_args,
)
from argparse import Namespace
from pathlib import Path


def test_sort_dict():
    """Test the _sort_dict function"""
    parser = ArgumentParser()
    parser._actions = []
    parser._action_groups = []

    # Case 1: Regular argument
    parser._actions.append(MagicMock(dest="arg1", help="Argument 1"))
    assert _sort_dict(("arg1", "value1"), parser, None) == 0

    # Case 2: Namespace
    assert _sort_dict(("arg1", Namespace()), parser, None) == 2

    # Case 3: Dict
    assert _sort_dict(("arg1", {}), parser, None) == 1

    # Case 4: NamespaceAction
    parser._actions.append(MagicMock(dest="arg2", spec=NamespaceAction))
    assert _sort_dict(("arg2", "value2"), parser, None) == 3

    # Case 5: _NamespaceArgumentGroup
    nag = MagicMock(spec=_NamespaceArgumentGroup)
    nag.name = "arg3"
    parser._action_groups.append(nag)
    assert _sort_dict(("arg3", "value3"), parser, None) == 4


def test_dump_dict():
    """Test the _dump_dict function"""
    parser = ArgumentParser()
    parser._actions = [MagicMock(dest="help", spec=HelpAction)]
    parser._action_groups = []

    # Case 1: Simple argument
    action1 = MagicMock(dest="arg1", help="Argument 1")
    parser._actions.append(action1)
    parsed_dict = {"arg1": "value1"}
    proc2group = {}
    procgroups = set()
    prefix = None
    result = _dump_dict(parsed_dict, parser, proc2group, procgroups, {}, prefix)
    assert result == ["# Argument 1\n", 'arg1 = "value1"\n', "\n"]

    # Case 2: Namespace argument
    action2 = MagicMock(dest="ns", spec=NamespaceAction, help="Namespace")
    parser._actions.append(action2)
    ns_arg = MagicMock(dest="ns.arg2", help="Argument 2")
    parser._actions.append(ns_arg)
    parsed_dict = {"ns": Namespace(arg2="value2")}
    result = _dump_dict(parsed_dict, parser, proc2group, procgroups, {}, prefix)
    assert result == [
        "# Namespace\n",
        "[ns]\n",
        "# Argument 2\n",
        'arg2 = "value2"\n',
        "\n",
    ]

    # Case 2.1: Namespace argument (envs)
    action2_1 = MagicMock(
        dest="envs",
        spec=_NamespaceArgumentGroup,
        help="Envs",
    )
    action2_1.name = "envs"
    parser._actions.append(action2_1)
    env_arg = MagicMock(
        dest="envs.arg2", help="Argument 2", type="json", default={"a": 1, "b": 2}
    )
    parser._actions.append(env_arg)
    parsed_dict = {"envs": Namespace(arg2={"a": 3})}
    name2proc = {"Process": MagicMock(envs_depth=2)}
    result = _dump_dict(parsed_dict, parser, {}, {}, name2proc, None)
    assert result == [
        "[envs]\n",
        "# Argument 2\n",
        "[envs.arg2]\na = 3\nb = 2\n",
        "\n",
    ]

    # Case 3: _NamespaceArgumentGroup (proc group)
    action3 = MagicMock(spec=_NamespaceArgumentGroup)
    action3.name = "group1"
    parser._action_groups.append(action3)
    group_arg = MagicMock(dest="group1.arg3", help="Argument 3")
    parser._actions.append(group_arg)

    parsed_dict = {
        "help": False,
        "group1": Namespace(arg3="value3"),
        "group1.arg3": "value3",
        "x": dict(y=1),
        "z": Path("/tmp"),
    }
    procgroups = {"group1"}
    result = _dump_dict(parsed_dict, parser, {}, procgroups, {}, None)
    assert result == [
        'z = "/tmp"\n',
        "\n",
        "[x]\ny = 1\n",
        "\n",
        "# +----------------------------------------------------------------------------+\n",  # noqa: E501
        "# | Arguments for process group: group1                                        |\n",  # noqa: E501
        "# +----------------------------------------------------------------------------+\n",  # noqa: E501
        "[group1]\n",
        "# Argument 3\n",
        'arg3 = "value3"\n',
        "\n",
    ]

    # Case 4: _NamespaceArgumentGroup (proc)
    action4 = MagicMock(spec=_NamespaceArgumentGroup)
    action4.name = "proc1"
    parser._action_groups.append(action4)
    proc_arg = MagicMock(dest="proc1.arg4", help="Argument 4")
    parser._actions.append(proc_arg)
    parser._actions.append(MagicMock(dest="dirsig", help="Directory signature"))
    parser._actions.append(MagicMock(dest="proc1.cache", help="Cache"))
    # parser._actions.append(
    #     MagicMock(dest="proc1.envs", help="Envs", spec=NamespaceAction)
    # )
    parser._actions.append(MagicMock(dest="proc1.envs.a", help="Env a"))

    parsed_dict = {
        "proc1": Namespace(
            arg4="value4", dirsig=False, cache=None, envs=Namespace(a=1)
        ),
        "proc1.arg4": "value4",
        "proc1.cache": None,
        "proc1.envs.a": 1,
        "dirsig": False,
    }
    procgroups = set()
    result = _dump_dict(parsed_dict, parser, {"proc1": None}, procgroups, {}, None)
    assert result == [
        "# +----------------------------------------------------------------------------+\n",  # noqa: E501
        "# | Arguments for process: proc1                                               |\n",  # noqa: E501
        "# +----------------------------------------------------------------------------+\n",  # noqa: E501
        "[proc1]\n",
        "# Argument 4\n",
        'arg4 = "value4"\n',
        "\n",
        "# (process level) Cache\n",
        "## cache = None\n",
        "\n",
        # '# Envs\n',  # proc.envs not defined as an action
        "[proc1.envs]\na = 1\n",
        "\n",
    ]

    # Case 4.1: _NamespaceArgumentGroup (proc)
    parser = ArgumentParser()
    parser._actions = [MagicMock(dest="help", spec=HelpAction)]
    parser._action_groups = []
    action4_1 = MagicMock(spec=_NamespaceArgumentGroup)
    action4_1.name = "proc1"
    parser._action_groups.append(action4_1)
    proc_envs = MagicMock(dest="proc1.envs", help="Argument envs", spec=NamespaceAction)
    parser._actions.append(proc_envs)
    parser._actions.append(
        MagicMock(
            dest="proc1.envs.a", help="Env a", type="json", default={"a": 0, "b": 2}
        )
    )

    parsed_dict = {
        "proc1": Namespace(envs=Namespace(a={"a": 1})),
        "proc1.envs.a": {"a": 1},
    }
    name2proc = {"proc1": MagicMock(envs_depth=2)}
    result = _dump_dict(parsed_dict, parser, {"proc1": None}, set(), name2proc, None)
    assert result == [
        "# +----------------------------------------------------------------------------+\n",  # noqa: E501
        "# | Arguments for process: proc1                                               |\n",  # noqa: E501
        "# +----------------------------------------------------------------------------+\n",  # noqa: E501
        "[proc1]\n",
        "# Argument envs\n",
        "[proc1.envs]\n",
        "# Env a\n",
        "[proc1.envs.a]\na = 1\nb = 2\n",
        "\n",
    ]


def test_dump_args(tmp_path: Path):
    """Test the dump_args function"""
    # Mock the parser
    parser = MagicMock()
    parser._actions = []
    action0 = MagicMock(spec=HelpAction, dest="help", help="Show this help message")
    action1 = MagicMock(dest="name", help="The name of the pipeline")
    action2 = MagicMock(dest="outdir", help="The output directory")
    action3 = MagicMock(dest="cache", help="Enable caching")
    action40 = MagicMock(
        spec=NamespaceAction, dest="group1", option_strings=["--group1"], help=None
    )
    action4 = MagicMock(dest="group1.param1", help="Parameter 1 for group1")
    parser._actions = [action0, action1, action2, action3, action40, action4]
    parser.get_action = lambda key, include_ns_group: {
        "help": action0,
        "name": action1,
        "outdir": action2,
        "cache": action3,
        "group1": action40,
        "group1.param1": action4,
    }[key]

    # Mock parsed args
    parsed_args = Namespace(
        name="test_pipeline",
        outdir=str(tmp_path / "output"),
        cache=True,
        group1=Namespace(param1="value1"),
    )

    # Create a temporary file
    dumped_file = tmp_path / "args.toml"

    proc = MagicMock(name="proc")
    proc.__meta__ = {"procgroup": MagicMock()}

    # Call the dump_args function
    dump_args(parser, parsed_args, dumped_file, [proc])

    # Check if the file exists
    assert dumped_file.exists()

    # Read the file and check the contents
    with open(dumped_file, "r") as f:
        content = f.read()

    assert "Show this help message" not in content
    assert "# The name of the pipeline" in content
    assert 'name = "test_pipeline"' in content
    assert "# The output directory" in content
    assert f'outdir = "{str(tmp_path / "output")}"' in content
    assert "# Enable caching" in content
    assert "cache = true" in content
    assert "# Parameter 1 for group1" in content
    assert 'param1 = "value1"' in content
