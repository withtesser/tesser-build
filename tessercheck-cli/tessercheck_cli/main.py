from __future__ import annotations

import sys
from typing import Final

import tessercheck.client as client
import tessercheck.component as component

_USAGE: Final[str] = "usage: tessercheck-check [--fix] [tree]"

_HERE: Final[str] = "."

_HELP: Final[frozenset[str]] = frozenset({"-h", "--help"})

_FIX: Final[str] = "--fix"


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] in _HELP:
        print(_USAGE)
        return 0
    fixing = _FIX in args
    operands = [arg for arg in args if arg != _FIX]
    if len(operands) > 1:
        print(f"unexpected extra arguments\n{_USAGE}", file=sys.stderr)
        return 2
    tree = operands[0] if operands else _HERE
    tessercheck = component.Tessercheck(component.Config(component.Spec()))
    try:
        if not fixing:
            check_tree_response = tessercheck.client.check_tree(client.CheckTreeRequest(tree=tree))
            for finding in check_tree_response.findings:
                print(finding)
            return 1 if check_tree_response.findings else 0
        fix_tree_response = tessercheck.client.fix_tree(client.FixTreeRequest(tree=tree))
    finally:
        tessercheck.close()
    print(
        f"fixed {len(fix_tree_response.fixed)} finding(s), "
        f"rewriting {fix_tree_response.files} file(s)"
    )
    for finding in fix_tree_response.fixed:
        print(f"fixed: {finding}")
    if fix_tree_response.remaining:
        print(f"{len(fix_tree_response.remaining)} finding(s) remain:")
        for finding in fix_tree_response.remaining:
            print(finding)
    return 1 if fix_tree_response.remaining else 0
