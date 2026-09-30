#!/usr/bin/env python3
"""Fill a red or green prompt template for one app tree.

    render_prompt.py --check <template> [--value name ...]
    render_prompt.py <template> <out> --root <worktree> [--example <dir>] --value name=value ...

The template's {name}s are run values, given with --value; {tree} is the app's
directory (story-drafting, or any rendered app), and it is also filled inside
include paths. Includes paste verbatim (run values are not filled inside them):

- {{FILE:path}}: a file of the worktree.
- {{SECTION:path#Heading}}: one "## Heading" section of such a file, to the next "## ".
- {{EXAMPLE:path}}: a file of the example tree (--example).
- {{AGENT_FILES}}: every tracked, non-empty Python file of {tree}/ with no
  generated mark, outside its acceptance tests: the files a red design leaves
  to green, which differ with the design.
- {{ROOT_TESTS}}: every acceptance test of {tree}/tests/ (test_*.py), each as a
  fenced block under its path.

A name, path, or heading that does not resolve is an error, and nothing is
written. --check only says whether every {name} is one of the --value names,
so a caller can refuse before it starts anything it would leave behind.
Used by scripts/baseline/prepare (trials) and scripts/app/prompt (direct).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

NAME = re.compile(r"(?<!\{)\{([a-z_]+)\}(?!\})")
PATH = r"(?:\{tree\}|[^{}])+"
TOKEN = re.compile(r"(\{\{(?:(?:FILE|SECTION|EXAMPLE):" + PATH + r"|AGENT_FILES|ROOT_TESTS)\}\})")
GENERATED = "# pragma: tesser-generated"


def names_outside_includes(template: str) -> set[str]:
    return set(NAME.findall(TOKEN.sub("", template)))


def render(template: str, values: dict[str, str], root: pathlib.Path, example: pathlib.Path | None) -> str:
    tree = values.get("tree", "")

    def fill(text: str) -> str:
        def value(match: re.Match[str]) -> str:
            if match.group(1) not in values:
                sys.exit(f"prompt: the template names {{{match.group(1)}}}, which is not a run value")
            return values[match.group(1)]
        return NAME.sub(value, text)

    def include(kind: str, target: str) -> str:
        target = target.replace("{tree}", tree)
        relative, _, heading = target.partition("#") if kind == "SECTION" else (target, "", "")
        base = example if kind == "EXAMPLE" else root
        if base is None:
            sys.exit(f"prompt: the template includes {kind}:{target}, and no example tree was given")
        path = base / relative
        if not path.is_file():
            sys.exit(f"prompt: the template includes {kind}:{target}, which is not a file")
        text = path.read_text()
        if kind == "SECTION":
            found = re.search(r"^## " + re.escape(heading) + r"[^\n]*\n.*?(?=^## |\Z)", text, re.M | re.S)
            if found is None:
                sys.exit(f"prompt: the template includes {kind}:{target}, which names no section")
            text = found.group(0)
        return text.rstrip("\n")

    def tracked(relative_dir: str) -> list[str]:
        listed = subprocess.run(["git", "ls-files", "--", "*.py"], cwd=root / tree, capture_output=True, text=True, check=True)
        return sorted(p for p in listed.stdout.split() if p.startswith(relative_dir))

    def fenced(relative: str) -> str:
        text = (root / tree / relative).read_text()
        return f"`{tree}/{relative}`:\n\n```python\n{text.rstrip(chr(10))}\n```"

    def agent_files() -> str:
        blocks = [fenced(p) for p in tracked("") if not p.startswith("tests/")
                  and (text := (root / tree / p).read_text()).strip() and not text.startswith(GENERATED)]
        if not blocks:
            sys.exit("prompt: the template includes AGENT_FILES, and the tree has none")
        return "\n\n".join(blocks)

    def root_tests() -> str:
        found = sorted(str(p.relative_to(root / tree)) for p in (root / tree / "tests").glob("test_*.py"))
        if not found:
            sys.exit("prompt: the template includes ROOT_TESTS, and the tree has no tests/test_*.py")
        return "\n\n".join(fenced(p) for p in found)

    out = []
    for part in TOKEN.split(template):
        if part == "{{AGENT_FILES}}":
            out.append(agent_files())
        elif part == "{{ROOT_TESTS}}":
            out.append(root_tests())
        elif token := re.fullmatch(r"\{\{(FILE|SECTION|EXAMPLE):(" + PATH + r")\}\}", part):
            out.append(include(token.group(1), token.group(2)))
        else:
            out.append(fill(part))
    return "".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("template")
    parser.add_argument("out", nargs="?")
    parser.add_argument("--root")
    parser.add_argument("--example")
    parser.add_argument("--value", action="append", default=[])
    args = parser.parse_args()
    template = pathlib.Path(args.template).read_text()
    pairs = [item.partition("=") for item in args.value]
    if args.check:
        unknown = sorted(names_outside_includes(template) - {name for name, _, _ in pairs})
        if unknown:
            sys.exit(f"prompt: the template names {', '.join('{' + n + '}' for n in unknown)}, which is not a run value")
        return
    if not args.out or not args.root:
        sys.exit("prompt: rendering needs <out> and --root")
    values = {name: value for name, _, value in pairs}
    text = render(template, values, pathlib.Path(args.root), pathlib.Path(args.example) if args.example else None)
    pathlib.Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
