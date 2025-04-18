from __future__ import annotations
from typing import TYPE_CHECKING, Any

from diot import Diot
from argx import Namespace
from argx.parser import _NamespaceArgumentGroup
from argx.action import HelpAction, NamespaceAction
from pipen.utils import get_marked, update_dict

from .defaults import PIPEN_ARGS

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path
    from argparse import ArgumentParser
    from pipen import Proc

# A value to indicate that the key is not found in the table
NULL_VAL = object()
# A value to indicate that the key is a namespace
NS_VAL = object()


def _sort_dict(
    item: tuple[str, Any],
    parser: ArgumentParser,
    prefix: str | None,
) -> int:
    """Sort the dictionary by the order of the arguments in the parser

    This is to make sure namespace, dict and namespace groups are sorted
    at the end of the toml table.

    Args:
        item: The item to sort
        parser: The parser instance
        prefix: The prefix for the keys

    Returns:
        The order of the item
    """
    key, value = item
    fullkey = f"{prefix}.{key}" if prefix else key
    action = parser.get_action(fullkey, include_ns_group=True)
    if isinstance(action, _NamespaceArgumentGroup):
        return 4
    if isinstance(action, NamespaceAction):
        return 3
    if isinstance(value, Namespace):
        return 2
    if isinstance(value, dict):
        return 1
    return 0


def _dump_dict(
    parsed_dict: dict,
    parser: ArgumentParser,
    proc2group: dict[str, str | None],
    procgroups: set[str],
    name2proc: dict[str, Proc],
    prefix: str | None,
) -> list[str]:
    """Dump the parsed arguments into a dictionary

    Args:
        parsed_dict: The parsed arguments
        parser: The parser instance
        proc2group: A dictionary mapping process names to their groups
        procgroups: A set of process groups
        prefix: The prefix for the keys

    Returns:
        A list of lines to write to the TOML file
    """
    out = []
    for key, value in sorted(
        parsed_dict.items(), key=lambda x: _sort_dict(x, parser, prefix)
    ):
        if "." in key or key.startswith("__"):
            continue

        fullkey = f"{prefix}.{key}" if prefix else key
        action = parser.get_action(fullkey, include_ns_group=True)

        if isinstance(action, HelpAction):
            continue

        if isinstance(action, NamespaceAction):
            if action.help:
                for line in action.help.splitlines():
                    out.append(f"# {line}\n")

            out.append(f"[{fullkey}]\n")
            out.extend(
                _dump_dict(
                    vars(value) if isinstance(value, Namespace) else value,
                    parser,
                    proc2group,
                    procgroups,
                    name2proc,
                    fullkey,
                )
            )
        elif isinstance(action, _NamespaceArgumentGroup):
            if fullkey in procgroups:
                decor = f"# +{'-' * max(len(fullkey), 76)}+\n"
                out.append(decor)
                out.append(f"# | Arguments for process group: {fullkey: <45} |\n")
                out.append(decor)
            elif fullkey in proc2group:
                procname = (
                    f"{proc2group[fullkey]}/{fullkey}"
                    if proc2group[fullkey]
                    else fullkey
                )
                decor = f"# +{'-' * max(len(procname), 76)}+\n"
                out.append(decor)
                out.append(f"# | Arguments for process: {procname: <51} |\n")
                out.append(decor)

            out.append(f"[{fullkey}]\n")
            out.extend(
                _dump_dict(
                    vars(value),
                    parser,
                    proc2group,
                    procgroups,
                    name2proc,
                    fullkey,
                )
            )
        elif not prefix and key in ("dirsig", "lang"):
            continue
        else:
            help = ""
            if action and action.help:
                help = action.help

            if prefix:
                paction = parser.get_action(prefix, include_ns_group=True)
                if (
                    isinstance(paction, _NamespaceArgumentGroup)
                    and paction.name in proc2group
                ):
                    if key in ("lang", "order", "dirsig", "in", "out"):
                        continue

                    if key in PIPEN_ARGS:
                        help = f"(process level) {help.splitlines()[0]}" if help else ""

                if (
                    isinstance(value, dict)
                    and not isinstance(value, Namespace)
                    and action
                    and action.type == "json"
                    and isinstance(action.default, dict)
                ):
                    proc0 = list(name2proc.values())[0]
                    # json options, make sure envs_depth applied
                    if (
                        # flattened
                        isinstance(paction, _NamespaceArgumentGroup)
                        and prefix == paction.name == "envs"
                        and proc0.envs_depth > 1
                    ):
                        value = update_dict(action.default, value, proc0.envs_depth - 1)
                    elif (
                        isinstance(paction, NamespaceAction)
                        and paction.dest.count(".") == 1
                        and paction.dest.endswith(".envs")
                    ):
                        pname = paction.dest.split(".")[0]
                        if (
                            pname in name2proc
                            and name2proc[pname].envs_depth
                            and name2proc[pname].envs_depth > 1
                        ):
                            value = update_dict(
                                action.default,
                                value,
                                name2proc[pname].envs_depth - 1,
                            )

            for line in help.splitlines():
                out.append(f"# {line}\n")

            if value is None:
                out.append(f"## {key} = None\n")

            elif isinstance(value, (Namespace, dict)):
                if isinstance(value, Namespace):
                    value = vars(value)
                if prefix:
                    val = {key: value}
                    for part in reversed(prefix.split(".")):
                        val = {part: val}
                    out.append(Diot(val).to_toml())
                else:
                    out.append(Diot({key: value}).to_toml())

            else:
                try:
                    out.append(Diot({key: value}).to_toml())
                except Exception:
                    out.append(Diot({key: str(value)}).to_toml())

            out.append("\n")

    return out


def dump_args(
    parser: ArgumentParser,
    parsed: Namespace,
    dumped_file: Path,
    procs: list[Proc],
) -> None:
    """Dump the parsed arguments into a dictionary

    Args:
        parser: The parser instance
        parsed: The parsed arguments
        dumped_file: The path to the TOML file
        procs: The processes in the pipeline
    """
    parsed_dict = vars(parsed)
    proc2group = {}
    procgroups = set()
    name2proc = {}
    for proc in procs:
        pg = get_marked(proc, "procgroup")
        pg = pg.name if pg else None
        proc2group[proc.name] = pg
        name2proc[proc.name] = proc
        if pg:
            procgroups.add(pg)

    out = _dump_dict(
        parsed_dict,
        parser,
        proc2group,
        procgroups,
        name2proc,
        prefix=None,
    )

    dumped_file.parent.mkdir(parents=True, exist_ok=True)
    with open(dumped_file, "w") as f:
        f.writelines(out)
