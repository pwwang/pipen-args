from __future__ import annotations

import sys
from typing import TYPE_CHECKING, List, Type
from abc import ABC

from diot import Diot
from argx import Namespace
from pipen.utils import is_loading_pipeline
from pipen.procgroup import ProcGroup as PipenProcGroup
from pipen_annotate import annotate

if TYPE_CHECKING:  # pragma: no cover
    from argx import ArgumentParser
    from pipen import Proc


class ProcGroup(PipenProcGroup, ABC):
    """Extend ProcGroup to add arguments to parser for process group

    We can't do it in plugin.on_init() hook, because we need the process
    group to be built first before the pipeline initialized. Usually, the
    pipeline needs some processes (typically start processes) to be built
    and use them as dependencies or dependent processes.
    """
    PRESERVED = PipenProcGroup.PRESERVED | {"parser"}

    def __init__(self, **opts) -> None:
        self.name: str = self.__class__.name or self.__class__.__name__
        # add arguments to parser
        parser = self.parser
        self._add_proggroup_args(parser)
        if (
            "-h" not in sys.argv
            and "--help" not in sys.argv
            and "-h+" not in sys.argv
            and "--help+" not in sys.argv
            and not is_loading_pipeline()
        ):
            # Leave the parser to add the arguments at `on_init` hook
            # So that we get a full help page with arguments from
            # all the processes
            parsed, rest = parser.parse_known_args(fromfile_keep=True)
            parser.set_cli_args(rest)
        else:
            parsed = Namespace()

        self.opts = Diot(self.__class__.DEFAULTS or {})
        parsed_opts = getattr(parsed, self.name, None) or {}
        if parsed_opts and isinstance(parsed_opts, Namespace):
            parsed_opts = vars(parsed_opts)
        parsed_opts.update(opts)
        self.opts.update(
            {k: v for k, v in parsed_opts.items() if v is not None}
        )

        self.starts: List[Type[Proc]] = []
        self.procs = Diot()
        self.post_init()
        self._load_runtime_procs()

    def post_init(self) -> None:
        """Post initialization

        This method is called after arguments are parsed and set to self.opts
        This method is called before runtime processes are loaded
        """
        pass

    @property
    def parser(self):
        """Pass arguments to initialize the parser

        The parser is a singleton and by default initalized at
        `plugin.on_init()` hook, which happens usually after the initialization
        of a process group.
        """
        from .parser_ import Parser
        return Parser()

    def _add_proggroup_args(self, parser: ArgumentParser) -> None:
        """Add process group arguments"""

        anno = annotate(self.__class__)

        parser.add_namespace(
            self.name,
            title=f"Process Group <{self.name}>",
        )

        parser.add_argument(
            f"--{self.name}",
            help="Process group opts, as a JSON string",
            action="ns",
        )

        for key, val in anno.Args.items():
            parser.add_argument(
                f"--{self.name}.{key}",
                help=val.help or "",
                **parser._get_arg_attrs_from_anno(val.attrs),
            )
