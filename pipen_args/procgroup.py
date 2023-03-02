from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from abc import ABC

from diot import Diot
from argx import Namespace
from pipen.procgroup import ProcGroup as PipenProcGroup
from pipen_annotate import annotate

if TYPE_CHECKING:  # pragma: no cover
    from argx import ArgumentParser


class ProcGroup(PipenProcGroup, ABC):
    """Extend ProcGroup to add arguments to parser for process group

    We can't do it in plugin.on_init() hook, because we need the process
    group to be built first before the pipeline initialized. Usually, the
    pipeline needs some processes (typically start processes) to be built
    and use them as dependencies or dependent processes.
    """
    PRESERVED = PipenProcGroup.PRESERVED | {"parser"}

    def __init__(self, **options) -> None:
        self.name = self.__class__.name or self.__class__.__name__

        # add arguments to parser
        parser = self.parser
        self._add_proggroup_args(parser)

        if (
            "-h" not in sys.argv
            and "--help" not in sys.argv
            and "-h+" not in sys.argv
            and "--help+" not in sys.argv
        ):
            parsed, rest = parser.parse_known_args()
            parser.set_cli_args(rest)
        else:
            parsed = Namespace()

        self.options = Diot(self.__class__.DEFAULTS or {})
        self.options.update(
            vars(getattr(parsed, self.name, None) or Namespace())
        )
        self.options |= (options or {})

        for method in self.__class__.__dict__.values():
            if callable(method) and getattr(method, "_defining_proc", False):
                method(self)

    @property
    def parser(self):
        """Pass arguments to initialize the parser

        The parser is a singleton and by default initalized at
        `plugin.on_init()` hook, which happens usually after the initialization
        of a process group.
        """
        from .parser import Parser
        return Parser()

    def _add_proggroup_args(self, parser: ArgumentParser) -> None:
        """Add process group arguments"""

        anno = annotate(self.__class__)
        if not anno.get("Args"):
            return

        parser.add_namespace(
            self.name,
            title=f"Process Group <{self.name}>",
        )

        parser.add_argument(
            f"--{self.name}",
            help="Process group options, as a JSON string",
            action="ns",
        )

        for key, val in anno.Args.items():
            parser.add_argument(
                f"--{self.name}.{key}",
                help=val.help or "",
                **parser._get_arg_attrs_from_anno(val.attrs),
            )
