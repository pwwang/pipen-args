import pytest
from pipen.utils import LOADING_ARGV0
from pipen_args import Parser
from pipen_args.parser_ import FallbackNamespace

from .conftest import with_argv


def test_parser_is_singleton():
    Parser() is Parser()


def test_fallbacknamespace():
    fbns = FallbackNamespace()
    fbns.a = 1
    assert fbns.a == 1

    fbns['b'] = 2
    assert fbns.b == 2

    assert fbns.x is None


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
