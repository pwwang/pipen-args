import pytest
from types import SimpleNamespace
from pipen import Proc
from pipen.utils import LOADING_ARGV0
from pipen_args import Parser
from pipen_args.parser_ import _pre_parse

from .conftest import fresh_parser, with_argv


def test_parser_is_singleton():
    Parser() is Parser()


def test_add_extra_argument():
    parser = Parser()
    with pytest.raises(ValueError, match='Extra arguments cannot be required'):
        parser.add_extra_argument('-x', required=True)


def test_parse_args_externally():
    parser = Parser()
    parser.add_extra_argument('-x', default=1)
    with pytest.raises(ValueError):
        parser.parse_args()

    with with_argv([LOADING_ARGV0]):
        p = parser.parse_extra_args()
    assert p.x == 1


def test_add_extra_argument_in_groups():
    parser = fresh_parser()
    parser.add_extra_argument("-x", group="Group 1")
    # Same group is reused
    parser.add_extra_argument("-y", group="Group 1")
    parser.add_extra_argument("-z")
    help_ = parser.format_help()
    assert "Group 1 (extra Options)" in help_
    assert "Extra Options" in help_
    assert "-x" in help_
    assert "-z" in help_


def test_set_cli_args_and_parse_args():
    parser = fresh_parser()
    parser.add_argument("-x", default=1)
    parser.set_cli_args(["-x", "5"])
    ns = parser.parse_args(_internal=True)
    assert ns.x == "5"
    # Parsed once only
    assert parser.parse_args(_internal=True) is ns


def test_parse_args_with_explicit_args():
    parser = fresh_parser()
    parser.add_argument("-x", default=1)
    ns = parser.parse_args(["-x", "7"], _internal=True)
    assert ns.x == "7"


def test_format_help_no_extra_groups():
    parser = fresh_parser()
    assert "Usage" in parser.format_help()
    assert "Usage" in parser.format_help(plus=False)


def test_pre_parse():
    """Test the `_pre_parse` function"""
    parser = fresh_parser()
    parser.add_namespace("foo", title="Foo")
    parser.add_argument("--foo", action="ns")
    parser.add_argument("--bar", type="json")
    parser.add_argument("--baz", default=1)

    args = [
        "plainarg",
        "--baz=5",
        "--foo.a", "1",
        "--foo.b[0].c", "2",
        "--foo.d[1]=3",
        "--foo.e", "--foo.f", "-1.2",
        "--foo.g",
        "--bar.x", "true",
        "--unknown", "x",
        "--foo.h",
    ]
    new_args = _pre_parse(parser, args, None)
    assert new_args == ["plainarg", "--baz=5", "--unknown", "x"]
    assert parser.get_action("foo").default == {
        "a": 1,
        "b": [{"c": 2}],
        "d": [None, 3],
        "e": True,
        "f": -1.2,
        "g": True,
        "h": True,
    }
    assert parser.get_action("bar").default == {"x": True}


def test_get_arg_attrs_from_anno():
    parser = fresh_parser()

    # Only the known keys are kept
    attrs = parser._get_arg_attrs_from_anno(
        {"help": "help text", "foo": "bar", "required": True}
    )
    assert attrs == {"help": "help text", "required": True}

    # hidden -> show=False
    attrs = parser._get_arg_attrs_from_anno({"hidden": True})
    assert attrs == {"show": False}

    # ns / namespace -> action ns
    attrs = parser._get_arg_attrs_from_anno({"ns": True})
    assert attrs["action"] == "ns"
    attrs = parser._get_arg_attrs_from_anno({"namespace": True})
    assert attrs["action"] == "ns"

    # flag -> store_true
    attrs = parser._get_arg_attrs_from_anno({"flag": True})
    assert attrs["action"] == "store_true"

    # array / list -> clear_extend
    attrs = parser._get_arg_attrs_from_anno({"array": True})
    assert attrs["action"] == "clear_extend"
    assert attrs["nargs"] == "+"
    attrs = parser._get_arg_attrs_from_anno({"list": True})
    assert attrs["action"] == "clear_extend"

    # choices=True -> terms
    attrs = parser._get_arg_attrs_from_anno({"choices": True}, terms={"a": 1})
    assert attrs["choices"] == ["a"]

    # choices=str -> split
    attrs = parser._get_arg_attrs_from_anno({"choices": "a,b"})
    assert attrs["choices"] == ["a", "b"]

    # choices + type -> typed choices
    attrs = parser._get_arg_attrs_from_anno({"choices": "1,2", "type": "json"})
    assert attrs["choices"] == [1, 2]


class _TestProc(Proc):
    """A test process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        x: x env
        y (required): y env
    """

    input = "a"
    output = "b:var"
    script = "echo {{in.a}}"
    envs = {"x": 1}


class _TestProcRequired(Proc):
    """A test process

    Input:
        a: input a

    Output:
        b: output b

    Envs:
        r (required): r env
    """

    input = "a"
    output = "b:var"
    script = "echo {{in.a}}"
    envs = {"r": "val"}
    cache = "force"


class _TestProcNoEnv(Proc):
    """A test process

    Input:
        a: input a

    Output:
        b: output b
    """

    input = "a"
    output = "b:var"
    script = "echo {{in.a}}"


class _TestProc2(Proc):
    """A second test process

    Input:
        a: input a
    """

    requires = _TestProc
    input = "a"
    script = "echo {{in.a}}"


def test_add_proc_args_non_flatten():
    parser = fresh_parser()
    parser._add_proc_args(_TestProc, is_start=True, hide=False, flatten=False)
    ns = parser.parse_args(
        [
            "--_TestProc.in.a",
            "1",
            "--_TestProc.envs.x",
            "5",
            "--_TestProc.forks",
            "2",
        ],
        _internal=True,
    )
    assert getattr(ns._TestProc, "in").a == ["1"]
    assert ns._TestProc.envs.x == "5"
    assert ns._TestProc.forks == 2


def test_add_proc_args_flatten():
    parser = fresh_parser()
    parser._add_proc_args(_TestProcRequired, is_start=True, hide=False, flatten=True)
    assert "Use `@configfile`" in parser.description
    ns = parser.parse_args(
        ["--in.a", "1", "--out.b", "x", "--envs.r", "5"],
        _internal=True,
    )
    assert getattr(ns, "in").a == ["1"]
    assert ns.out.b == "x"
    assert ns.envs.r == "5"


def test_add_proc_args_hide_and_procgroup():
    parser = fresh_parser()
    _TestProc.__meta__["procgroup"] = SimpleNamespace(name="PG")
    try:
        parser._add_proc_args(_TestProc, is_start=False, hide=True, flatten=False)
        # The start process is hidden, so no input arguments
        assert parser.get_action("_TestProc.in.a", include_ns_group=True) is None
        assert "Process <PG/_TestProc>" in parser.format_help()
    finally:
        _TestProc.__meta__["procgroup"] = None


def test_add_proc_args_no_nexts():
    # With nexts, no output arguments
    parser = fresh_parser()
    parser._add_proc_args(_TestProc2, is_start=False, hide=False, flatten=False)
    assert parser.get_action("_TestProc2.out.b", include_ns_group=True) is None
    # Without envs, no envs arguments
    parser = fresh_parser()
    parser._add_proc_args(_TestProcNoEnv, is_start=False, hide=False, flatten=False)
    assert parser.get_action("_TestProcNoEnv.envs", include_ns_group=True) is None


def test_add_proc_args_with_defaults():
    parser = fresh_parser()
    parser._add_proc_args(_TestProcRequired, is_start=False, hide=False, flatten=False)
    action = parser.get_action("_TestProcRequired.cache", include_ns_group=True)
    assert action is not None and action.default == "force"


def test_add_envs_arguments():
    from diot import Diot

    parser = fresh_parser()
    ns = parser.add_namespace("proc", title="Proc")
    anno = {
        "x": SimpleNamespace(attrs={"type": "json"}, terms={}, help="x help"),
        "w": SimpleNamespace(
            attrs={"action": "ns"},
            terms={
                "a": SimpleNamespace(attrs={"default": 1}, terms={}, help="a help")
            },
            help="w help",
        ),
    }
    parser._add_envs_arguments(
        ns, anno, {"x": 1, "w": Diot({"a": 2})}, False, "proc"
    )
    parsed = parser.parse_args(["--proc.envs.x", "3"], _internal=True)
    assert parsed.proc.envs.x == 3
