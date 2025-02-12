import pytest  # noqa: F401
from unittest.mock import MagicMock
from argx.action import NamespaceAction
from argx.parser import _ArgumentGroup, _NamespaceArgumentGroup
from pipen_args.plugin import _dump_dict, _sort_actions, _procs_and_groups, dump_args
from argparse import Namespace
from pathlib import Path


def test_dump_dict():
    """Test the _dump_dict function"""
    test_dict = {
        "key1": "value1",
        "key2": 123,
        "key3": True,
        "key4": {"subkey1": "subvalue1", "subkey2": 456},
        "key-with-dash": "value-with-dash",
        "key with space": "value with space",
    }
    expected_output = (
        '{ key1 = "value1", key2 = 123, key3 = true, '
        'key4 = { subkey1 = "subvalue1", subkey2 = 456 }, '
        'key-with-dash = "value-with-dash", '
        '"key with space" = "value with space" }'
    )
    assert _dump_dict(test_dict) == expected_output


def test_sort_actions():
    """Test the _sort_actions function"""
    # Mock the Action objects
    action1 = MagicMock(dest="action1")
    action2 = MagicMock(dest="action2")
    action3 = MagicMock(dest="action3")
    action4 = NamespaceAction(dest="action4", option_strings=["--action4"])
    action41 = MagicMock(dest="action4.action41")
    action5 = MagicMock(dest="proc1.action5")
    action6 = MagicMock(dest="proc2.action6")
    action61 = NamespaceAction(dest="proc2.action61", option_strings=["--action61"])
    action62 = MagicMock(dest="proc2.action61.x")
    action7 = MagicMock(dest="workdir")  # Ignored dest
    action8 = MagicMock(dest="group1.action8")
    action9 = NamespaceAction(dest="group1.action9", option_strings=["--action9"])
    action10 = MagicMock(dest="group1")
    action11 = MagicMock(dest="proc1")

    actions = [
        action1,
        action2,
        action3,
        action4,
        action41,
        action5,
        action6,
        action61,
        action62,
        action7,
        action8,
        action9,
        action10,
        action11,
    ]
    procgroups = {"group1": {"base": 100000, "procs": ["proc1"]}}
    procs = {"proc1": {"base": 110000, "group": "group1"}, "proc2": {"base": 10000}}

    # Call the _sort_actions function
    sorted_actions = _sort_actions(actions, procgroups, procs)

    # Assert that the actions are sorted correctly
    assert action1.index == 1
    assert action2.index == 1
    assert action3.index == 1
    assert action4.index == 9000
    assert action41.index == 9001
    assert action5.index == 110001
    assert action6.index == 10001
    assert action61.index == 19000
    assert action62.index == 19001
    assert action7.index is None
    assert action8.index == 100001
    assert action9.index == 190000
    assert action10.index == 100000
    assert action11.index == 110000

    assert sorted_actions == [
        action1,
        action2,
        action3,
        action4,
        action41,
        action6,
        action61,
        action62,
        action10,
        action8,
        action11,
        action5,
        action9,
    ]


def test_procs_and_groups_args_flatten_false():
    """Test the _procs_and_groups function with args_flatten=False"""
    # Mock the parser
    parser = MagicMock()
    parser._action_groups = []

    # Call the _procs_and_groups function with args_flatten=False
    procgroups, procs = _procs_and_groups(parser, False, None, None)

    # Assert that the procs and procgroups are empty
    assert procgroups == {}
    assert procs == {}


def test_procs_and_groups_args_flatten_true():
    """Test the _procs_and_groups function with args_flatten=True"""
    # Mock the parser
    parser = MagicMock()
    parser._action_groups = []

    # Call the _procs_and_groups function with args_flatten=True
    procgroups, procs = _procs_and_groups(parser, True, "proc1", "group1")

    # Assert that the procs and procgroups are created correctly
    assert "group1" in procgroups
    assert "proc1" in procs
    assert procs["proc1"]["group"] == "group1"


def test_procs_and_groups_with_action_groups():
    """Test the _procs_and_groups function with action groups"""
    # Mock the parser
    parser = MagicMock()

    # Create mock action groups
    group1 = MagicMock(spec=_ArgumentGroup, title="Process Group <group1>")
    group1.name = "group1"
    group1._group_actions = []  # Add this line
    group2 = MagicMock(spec=_NamespaceArgumentGroup, title="Process <group1/proc1>")
    group2.name = "proc1"
    group3 = MagicMock(spec=_ArgumentGroup, title="Other Group")
    group3.name = "other"
    parser._action_groups = [group1, group2, group3]

    # Call the _procs_and_groups function
    procgroups, procs = _procs_and_groups(parser, False, None, None)

    # Assert that the procs and procgroups are created correctly
    assert "group1" in procgroups
    assert "proc1" in procs
    assert procs["proc1"]["group"] == "group1"


def test_procs_and_groups_with_action_groups_flattened():
    """Test the _procs_and_groups function with action groups and flattened args"""
    # Mock the parser
    parser = MagicMock()

    # Create mock action groups
    group1 = MagicMock(spec=_ArgumentGroup, title="Process Group <group1>")
    group1.name = "group1"
    group1._group_actions = []  # Add this line
    group2 = MagicMock(spec=_NamespaceArgumentGroup, title="Process <group1/proc1>")
    group2.name = "proc1"
    group3 = MagicMock(spec=_ArgumentGroup, title="Other Group")
    group3.name = "other"
    parser._action_groups = [group1, group2, group3]

    # Call the _procs_and_groups function
    procgroups, procs = _procs_and_groups(parser, True, "proc1", "group1")

    # Assert that the procs and procgroups are created correctly
    assert "group1" in procgroups
    assert "proc1" in procs
    assert procs["proc1"]["group"] == "group1"


def test_procs_and_groups_process_group_title():
    """Test the _procs_and_groups function with Process Group title"""
    # Mock the parser
    parser = MagicMock()

    # Create mock action groups
    group1 = MagicMock(spec=_NamespaceArgumentGroup, title="Process Group <group1>")
    group1.name = "group1"
    group2 = MagicMock(spec=_NamespaceArgumentGroup, title="Process <group2>")
    group2.name = "group2"
    parser._action_groups = [group1, group2]

    # Call the _procs_and_groups function
    procgroups, procs = _procs_and_groups(parser, False, None, None)

    # Assert that the procs and procgroups are created correctly
    assert procgroups == {'group1': {'base': 1000000, 'procs': [], 'used': False}}
    assert procs == {'group2': {'group': None, 'used': False, 'base': 10000}}


def test_procs_and_groups_process_group_title_flattened():
    """Test the _procs_and_groups function with Process Group title and flattened args"""
    # Mock the parser
    parser = MagicMock()

    # Create mock action groups
    group1 = MagicMock(spec=_ArgumentGroup, title="Process Group <mygroup>")
    group1.name = "mygroup"
    parser._action_groups = [group1]

    # Call the _procs_and_groups function
    procgroups, procs = _procs_and_groups(parser, True, "proc1", "mygroup")

    # Assert that the procs and procgroups are created correctly
    assert "mygroup" in procgroups
    assert "proc1" in procs
    assert procs["proc1"]["group"] == "mygroup"


def test_dump_args(tmp_path: Path):
    """Test the dump_args function"""
    # Mock the parser
    parser = MagicMock()
    parser._actions = []
    action1 = MagicMock(dest="name", help="The name of the pipeline")
    action2 = MagicMock(dest="outdir", help="The output directory")
    action3 = MagicMock(dest="cache", help="Enable caching")
    action40 = NamespaceAction(dest="group1", option_strings=["--group1"])
    action4 = MagicMock(dest="group1.param1", help="Parameter 1 for group1")
    parser._actions = [action1, action2, action3, action40, action4]

    # Mock parsed args
    parsed_args = Namespace(
        name="test_pipeline",
        outdir=str(tmp_path / "output"),
        cache=True,
        **{"group1.param1": "value1"},
    )

    # Create a temporary file
    dumped_file = tmp_path / "args.toml"

    # Call the dump_args function
    dump_args(parser, parsed_args, dumped_file, False, None, None)

    # Check if the file exists
    assert dumped_file.exists()

    # Read the file and check the contents
    with open(dumped_file, "r") as f:
        content = f.read()

    assert "# The name of the pipeline" in content
    assert 'name = "test_pipeline"' in content
    assert "# The output directory" in content
    assert f'outdir = "{str(tmp_path / "output")}"' in content
    assert "# Enable caching" in content
    assert "cache = true" in content
    assert "# Parameter 1 for group1" in content
    assert 'param1 = "value1"' in content
