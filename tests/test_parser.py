import pytest  # noqa: F401
from pipen_args import Parser


def test_parser_is_singleton():
    Parser()
    with pytest.raises(ValueError):
        Parser()
