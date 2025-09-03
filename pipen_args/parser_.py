"""Command line argument parser for pipen"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Sequence, Type, Mapping

from argx import ArgumentParser, Namespace
from argx.parser import _ArgumentGroup
from argx.utils import format_title
from diot import Diot

# from pipen.utils import is_loading_pipeline
from pipen_annotate import annotate

from .defaults import PIPELINE_ARGS_GROUP, FLATTEN_PROC_ARGS, PIPEN_ARGS

if TYPE_CHECKING:  # pragma: no cover
    from argparse import Action
    from pipen import Pipen, Proc


class ParserMeta(type):
    """Meta class for Proc"""

    _INST = None

    def __call__(cls, *args, **kwds) -> Parser:
        """Make sure Parser class is singleton

        Args:
            *args: and
            **kwds: Arguments for the constructor

        Returns:
            The Parser instance
        """
        if cls._INST is None:
            cls._INST = super().__call__(*args, **kwds)

        return cls._INST


class Parser(ArgumentParser, metaclass=ParserMeta):
    """Subclass of ArgumentParser to fit for pipen pipeline"""

    def __init__(self, *args, **kwargs) -> None:
        """Create a parser for pipen pipeline.

        See <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>
        for the arguments and keyword arguments.

        Args:
            *args: Arguments for the ArgumentParser
            **kwargs: Keyword arguments for the ArgumentParser
                Note that `add_help`, `fromfile_prefix_chars`, `usage` and
                `allow_abbrev`.
                are set by default and cannot be changed.
                The default `usage` is `%(prog)s [-h | -h+] [options]`.
                The default `allow_abbrev` is `False`.
                The default `add_help` is `["h", "help", "h+", "help+"]`.
                The default `fromfile_prefix_chars` is `@
        """
        kwargs["add_help"] = ["h", "help", "h+", "help+"]
        kwargs["fromfile_prefix_chars"] = "@"
        kwargs["usage"] = "%(prog)s [-h | -h+] [options]"
        kwargs["allow_abbrev"] = False
        super().__init__(*args, **kwargs)

        self.flatten_proc_args: bool | str | None = None
        self._cli_args = None
        self._pipeline_args_group = None
        self._parsed = None
        # A separate parser to hold extra arguments only
        self._extra_parser = ArgumentParser(add_help=False, fromfile_prefix_chars="@")
        # Registry of explicitly created extra-argument groups by title
        self._extra_groups: dict[str, _ArgumentGroup] = {}

    def add_extra_argument(
        self,
        *args,
        group: str | None = None,
        **kwargs,
    ) -> Action:
        """Add an extra argument (other than the pipeline arguments).

        Args:
            *args: The argument flags
            group: The title of the extra-argument group to add this argument into.
                If None, the argument is added to the default extra-argument group.
            **kwargs: The keyword arguments for `add_argument`.
                You may optionally pass `group` (str) to add the argument into a
                titled extra-argument group.

        Returns:
            The added action
        """
        if kwargs.get("required", False) is True:
            raise ValueError("Extra arguments cannot be required.")

        # Support assigning to a named extra group via `group="Title"`
        group = f"{group} (extra options)" if group else "Extra Options"
        if group not in self._extra_groups:
            grp = self._extra_parser.add_argument_group(group)
            self._extra_groups[group] = grp
        else:
            grp = self._extra_groups[group]

        return grp.add_argument(*args, **kwargs)

    def set_cli_args(self, args: Any) -> None:
        """Set cli arguments, allows externals to set arguments to parse

        Args:
            args: The CLI arguments to parse
        """
        self._cli_args = args

    def parse_args(  # type: ignore[override]
        self,
        args: Any = None,
        _internal: bool = False,
        namespace: Any = None,
    ) -> Namespace:
        """Parse the pipeline arguments.

        This is used internally.

        Args:
            args: The arguments to parse.
            _internal: Whether this is called internally.
                This is used to make sure the arguments are parsed at the right time.
                When users actually want to parse the extra arguments, they should
                call `parse_extra_args` instead.
            namespace: The namespace to parse into.

        Returns:
            The parsed namespace.
        """
        if not _internal:
            raise ValueError("Please use `parse_extra_args` to parse extra arguments.")

        if not self._parsed:
            # This should be called only once at `on_init` hook
            # If you have additional arguments, before `on_init`
            # You should call `parse_known_args` instead
            if self._cli_args is not None:
                args = self._cli_args

            self._parsed = super().parse_args(args, namespace)
        return self._parsed

    def parse_extra_args(
        self,
        args: Sequence[str] | None = None,
        fromfile_parse: bool = True,
        fromfile_keep: bool = True,
    ) -> Namespace:
        """Parse extra arguments.

        When `-h`, `-h+`, `--help` or `--help+` is in the sys.argv,
        do not parse the arguments, and leave them to the `on_init` hook.
        If `args` is passed, they are anyway parsed, which means if there are
        `-h`, `-h+`, `--help` or `--help+` in `args`, the program will be terminated
        here with the trancated help message. Because the arguments won't be futher
        parsed in the `on_init` hook.

        Args:
            args: The arguments to parse
            fromfile_parse: Whether to parse the extra arguments from file (`@file`)
                when we are not just loading the pipeline.
            fromfile_keep: Whether to keep the `@file` arguments in the remaining args.

        Returns:
            The parsed namespace.
        """
        args = args or self._cli_args or sys.argv[1:]

        # Parse only the extra arguments, leave the rest to the main parser later
        ns, remaining = self._extra_parser.parse_known_args(
            args,
            fromfile_parse=fromfile_parse,
            fromfile_keep=fromfile_keep,
        )
        # Save remaining args so the main parser can consume them
        self._cli_args = remaining  # type: ignore[assignment]
        return ns

    def init(self, pipen: Pipen) -> None:
        """Define arguments"""
        self._pipeline_args_group = self.add_argument_group(  # type: ignore[assignment]
            pipen._kwargs["plugin_opts"].get(
                "args_group",
                PIPELINE_ARGS_GROUP,
            ),
            order=-99,
        )
        self.flatten_proc_args = pipen._kwargs["plugin_opts"].get(
            "args_flatten",
            FLATTEN_PROC_ARGS,
        )

        pipen.build_proc_relationships()
        if len(pipen.procs) > 1 and self.flatten_proc_args is True:
            raise ValueError(  # pragma: no cover
                "Cannot flatten process arguments for multiprocess pipeline."
            )

        if self.flatten_proc_args == "auto":
            self.flatten_proc_args = (
                len(pipen.procs) == 1 and not pipen.procs[0].__meta__["procgroup"]
            )

        for arg, argopt in PIPEN_ARGS.items():
            if arg == "order":
                continue

            if arg == "outdir":
                argopt["default"] = pipen.outdir
            elif arg == "name":
                argopt["default"] = pipen.name

            if arg in ("scheduler_opts", "plugin_opts"):
                if self.flatten_proc_args:
                    argopt["default"] = Diot(pipen._kwargs.get(arg, None) or {}) | (
                        getattr(pipen.procs[0], arg, None) or {}
                    )
                else:
                    argopt["default"] = pipen._kwargs.get(arg, None) or {}

            self._pipeline_args_group.add_argument(f"--{arg}", **argopt)

        if self.flatten_proc_args is True:
            self._add_proc_args(
                pipen.procs[0],
                is_start=True,
                hide=False,
                flatten=True,
            )
        else:
            for i, proc in enumerate(pipen.procs):
                in_procgroup = bool(proc.__meta__["procgroup"])
                self._add_proc_args(
                    proc,
                    is_start=(
                        (proc in pipen.starts)  # type: ignore[operator]
                        and not in_procgroup
                    ),
                    hide=(
                        in_procgroup
                        if not proc.plugin_opts
                        else proc.plugin_opts.get("args_hide", in_procgroup)
                    ),
                    flatten=False,
                    order=i,
                )
            self.description = (
                f"{self.description or ''}\n"  # type: ignore[has-type]
                "Use `@configfile` to load default values for the options."
            )

    def _get_arg_attrs_from_anno(
        self,
        anno_attrs: Mapping[str, Any],
        terms: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """Get argument attributes from annotation"""
        out = {
            k: v
            for k, v in anno_attrs.items()
            if k
            in (
                "help",
                "action",
                "nargs",
                "default",
                "dest",
                "required",
                "metavar",
                "choices",
                "type",
            )
        }
        if "hidden" in anno_attrs:
            out["show"] = False

        # Add some shotcuts
        if anno_attrs.get("ns") or anno_attrs.get("namespace"):
            out.setdefault("action", "ns")
        if anno_attrs.get("flag"):
            out.setdefault("action", "store_true")
        if anno_attrs.get("array") or anno_attrs.get("list"):
            out.setdefault("action", "clear_extend")
            out.setdefault("nargs", "+")

        typefun = None
        if out.get("type"):
            typefun = self._registry_get("type", out["type"], out["type"])

        choices = out.get("choices", None)
        if choices is True:
            out["choices"] = list(terms)
        elif isinstance(choices, str):
            out["choices"] = choices.split(",")

        if out.get("choices") and typefun:
            out["choices"] = [typefun(c) for c in out["choices"]]

        return out

    def _add_proc_args(
        self,
        proc: Type[Proc],
        is_start: bool,
        hide: bool,
        flatten: bool,
        order: int = 0,
    ) -> None:
        """Add process arguments"""
        if is_start:
            hide = False

        anno = annotate(proc)

        if not flatten:
            name = (
                f"{proc.__meta__['procgroup'].name}/{proc.name}"
                if proc.__meta__["procgroup"]
                else proc.name
            )
            # add a namespace argumemnt for this proc
            self.add_namespace(
                proc.name,
                title=f"Process <{name}>",
                show=not hide,
                order=order + 1,  # avoid 0 conflicting default
            )
        else:
            self.description = (
                f"{anno.Summary.short}\n{anno.Summary.long}\n"
                "Use `@configfile` to load default values for the options."
            )

        if is_start:
            for inkey, inval in anno.Input.items():
                self.add_argument(
                    f"--in.{inkey}" if flatten else f"--{proc.name}.in.{inkey}",
                    help=inval.help or "",
                    **self._get_arg_attrs_from_anno(inval.attrs),
                )

        if not proc.nexts:
            for key, val in anno.Output.items():
                self.add_argument(
                    f"--out.{key}" if flatten else f"--{proc.name}.out.{key}",
                    help=val.help or "",
                    **self._get_arg_attrs_from_anno(val.attrs),
                )

        if proc.envs:
            self.add_argument(
                "--envs" if flatten else f"--{proc.name}.envs",
                action="ns",
                help="Environment variables for the process",
                default=Diot(proc.envs),
            )

        self._add_envs_arguments(
            self,  # type: ignore[arg-type]
            anno.Envs,
            proc.envs or {},
            flatten,
            proc.name,
        )

        if not flatten:
            for key in (
                "cache",
                "dirsig",
                "lang",
                "error_strategy",
                "num_retries",
                "scheduler",
                "forks",
                "order",
            ):
                attrs = PIPEN_ARGS[key].copy()
                proc_default = getattr(proc, key, None)
                pipen_default = PIPEN_ARGS[key].get("default", None)
                if proc_default is not None:
                    attrs["default"] = proc_default
                elif pipen_default is not None:
                    attrs["default"] = pipen_default

                self.add_argument(f"--{proc.name}.{key}", **attrs)

            for key in ("plugin_opts", "scheduler_opts"):
                self.add_argument(
                    f"--{proc.name}.{key}",
                    default=getattr(proc, key),
                    **{k: v for k, v in PIPEN_ARGS[key].items() if k != "default"},
                )

    def _add_envs_arguments(
        self,
        ns: Namespace,
        anno: Mapping[str, Any],
        values: Mapping[str, Any],
        flatten: bool,
        proc_name: str,
        key: str = "envs",
    ) -> None:
        """Add the envs argument to the namespace"""
        for kk, vv in anno.items():
            if kk not in values:
                continue

            default = values[kk]
            if default is not None:
                vv.attrs["default"] = default
                # If we have a default value, we don't need to require it
                if vv.attrs.get("required"):
                    vv.attrs["required"] = False

            attrs = self._get_arg_attrs_from_anno(vv.attrs, vv.terms)
            ns.add_argument(
                f"--{key}.{kk}" if flatten else f"--{proc_name}.{key}.{kk}",
                help=vv.help or "",
                **attrs,
            )

            # add sub-namespace
            if attrs.get("action", None) in ("namespace", "ns"):
                self._add_envs_arguments(
                    ns=ns,
                    anno=vv.terms,
                    values=default,
                    flatten=flatten,
                    proc_name=proc_name,
                    key=f"{key}.{kk}",
                )

    # Compose help from main parser plus extra parser's actions/groups
    def format_help(self, plus: bool = True) -> str:
        main_help = super().format_help(plus=plus)

        if not self._extra_groups:
            return main_help

        formatter = self._get_formatter()
        for action_group in sorted(
            self._extra_groups.values(),
            key=lambda x: (x.order, x.title),  # type: ignore[return-value]
        ):
            formatter.start_section(
                "\033[1m\033[4m"
                f"{format_title(action_group.title)}"  # type: ignore[arg-type]
                "\033[0m\033[0m"
            )
            formatter.add_text(action_group.description)
            formatter.add_arguments(  # type: ignore[call-arg]
                action_group._group_actions,
                plus,  # type: ignore[arg-type]
            )
            formatter.end_section()

        return main_help + "\n" + formatter.format_help()
