"""Regression test for a percent sign in a declared output value

The declared output value is appended to the help of the `--out.<key>`
argument. Since argparse %-formats every help string, a bare percent sign in
that value used to make rendering the help crash.
"""
from pipen import Proc

from .conftest import fresh_parser


class P(Proc):
    """A process with a percent sign in the declared output

    Output:
        r: the report
    """

    input = "a"
    output = "r:file:report_%i.txt"
    script = "echo x"


def test_help_percent_in_declared_output():
    parser = fresh_parser()
    parser._add_proc_args(P, is_start=True, hide=False, flatten=False)
    help_ = parser.format_help()
    assert "[default: report_%i.txt]" in help_
    assert "%%" not in help_
