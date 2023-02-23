"""Command line argument parser for pipen"""
from __future__ import annotations

from typing import TYPE_CHECKING, Type

from argx import ArgumentParser
from pipen_annotate import annotate

from .utils import (
    PIPELINE_ARGS_GROUP,
    FLATTEN_PROC_ARGS,
    PIPEN_ARGS,
    _get_argument_attrs,
    _add_envs_arguments,
)

if TYPE_CHECKING:
    from pipen import Pipen, Proc


class Parser(ArgumentParser):
    """Subclass of Params to fit for pipen

    Args:
        pipeline_args_group: The group name to gather all the parameters on
            help page
        hidden_args: Hide some arguments in help page
    """

    INST = None

    def __new__(
        cls,
        *args,
        pipeline_args_group: str = PIPELINE_ARGS_GROUP,
        flatten_proc_args: bool | str = FLATTEN_PROC_ARGS,
        **kwargs,
    ) -> Parser:
        """Make class as singleton

        As we want external instantiation returns the same instance.
        """
        if cls.INST is None:
            cls.INST = super().__new__(cls)
            return cls.INST

        raise ValueError(
            "Class Parser should only instantiate once. \n"
            "If you want to access the instance, use `Parser.INST` or "
            "`from pipen_args import parser`"
        )

    def __init__(
        self,
        *args,
        pipeline_args_group: str = PIPELINE_ARGS_GROUP,
        flatten_proc_args: bool | str = FLATTEN_PROC_ARGS,
        **kwargs,
    ) -> None:
        """Constructor"""
        if getattr(self, "_inited", False):
            return

        kwargs["add_help"] = "+"
        kwargs["fromfile_prefix_chars"] = "@"
        super().__init__(*args, **kwargs)

        self.flatten_proc_args = flatten_proc_args
        self._pipeline_args_group = self.add_argument_group(
            pipeline_args_group,
            order=-99,
        )

    def init(self, pipen: Pipen) -> None:
        """Define arguments"""
        pipen.build_proc_relationships()
        if len(pipen.procs) > 1 and self.flatten_proc_args is True:
            raise ValueError(
                "Cannot flatten process arguments for multiprocess pipeline."
            )

        if self.flatten_proc_args == "auto":
            self.flatten_proc_args = len(pipen.procs) == 1

        config = pipen.config
        if self.flatten_proc_args:
            config = config.copy()
            for opt in (
                "lang",
                "cache",
                "dirsig",
                "error_strategy",
                "num_retries",
                "forks",
                "submission_batch",
                "scheduler",
                "scheduler_opts",
                "plugin_opts",
            ):
                value = getattr(pipen.procs[0], opt, None)
                if value is not None:
                    config[opt] = value

        for arg, argopt in PIPEN_ARGS.items():
            if arg in ("order", "export"):
                continue

            if arg == "outdir":
                argopt["default"] = pipen.outdir
            elif arg == "name":
                argopt["default"] = pipen.name

            self._pipeline_args_group.add_argument(f"--{arg}", **argopt)

        if self.flatten_proc_args is True:
            self._add_proc_args(
                pipen.procs[0],
                is_start=True,
                hide=False,
                flatten=True,
            )
        else:
            for proc in pipen.procs:
                self._add_proc_args(
                    proc,
                    is_start=proc in pipen.starts,
                    hide=(
                        False
                        if not proc.plugin_opts
                        else proc.plugin_opts.get("args_hide", False)
                    ),
                    flatten=False,
                )
            self.description = (
                f"{self.description or ''}\n"
                "Use `@configfile` to load default values for the options."
            )

    def _add_proc_args(
        self,
        proc: Type[Proc],
        is_start: bool,
        hide: bool,
        flatten: bool,
    ) -> None:
        """Add process arguments"""
        if is_start:
            hide = False

        proc = annotate(proc)
        anno = proc.annotated

        if not flatten:
            # add a namespace argumemnt for this proc
            self.add_namespace(
                proc.name,
                description=anno.Summary.short,
                show=not hide,
            )
        else:
            self.description = (
                f"{anno.Summary.short}\n{anno.Summary.long}\n"
                "Use `@configfile` to load default values for the options."
            )

        if is_start:
            in_ns = self.add_namespace(
                "in" if flatten else f"{proc.name}.in",
                description="Input data for the process.",
                show=not hide,
            )

            for inkey, inval in anno.Input.items():
                in_ns.add_argument(
                    f"--in.{inkey}"
                    if flatten
                    else f"--{proc.name}.in.{inkey}",
                    **_get_argument_attrs(inval.attrs),
                )

        if not proc.nexts:
            out_ns = self.add_namespace(
                "out" if flatten else f"{proc.name}.out",
                description=(
                    "Output for the process (can't be overwritten, just FYI)."
                ),
                show=False,
            )

            for key, val in anno.Output.items():
                out_ns.add_argument(
                    f"--out.{key}" if flatten else f"--{proc.name}.out.{key}",
                    **_get_argument_attrs(val.attrs),
                )

        envs_ns = self.add_namespace(
            "envs" if flatten else f"{proc.name}.envs",
            description="Envs for the process.",
            show=not hide,
        )
        _add_envs_arguments(
            envs_ns,
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
                "forks",
                "submission_batch",
                "order",
                "export",
            ):
                attrs = PIPEN_ARGS[key]
                default = getattr(proc, key)
                if default is not None:
                    attrs["default"] = default

                self.add_argument(f"--{proc.name}.{key}", **attrs)

            for key in ("plugin_opts", "scheduler_opts"):
                self.add_argument(f"--{proc.name}.{key}", **PIPEN_ARGS[key])
