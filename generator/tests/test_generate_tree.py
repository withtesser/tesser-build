from __future__ import annotations

import pathlib
import re
import tomllib

import tesser.testing as ts


class TestGeneratingTrees:

    def test_every_committed_spec_generates_every_template_its_guards_open_and_exits_zero(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[1]
        guards = {
            template.relative_to(tree / "templates").as_posix(): frozenset(
                re.findall(r"\{\{#([a-z_]+)\}\}", template.relative_to(tree / "templates").as_posix())
            )
            for template in (tree / "templates").rglob("*.tmpl")
        }
        opened = {
            spec.stem: frozenset(
                (f"storage_{stated.get('storage', 'postgres')}", f"host_{stated.get('host', 'cli')}")
            )
            for spec in sorted((tree / "specs").glob("*.toml"))
            for stated in (tomllib.loads(spec.read_text()),)
        }
        cli = ts.Cli("srv.cli.generate")

        answered = {
            spec.stem: cli.run(str(spec), str(tmp_path / spec.stem))
            for spec in sorted((tree / "specs").glob("*.toml"))
        }

        assert answered
        assert {name: (cli_answer.exit_code, cli_answer.stderr) for name, cli_answer in answered.items()} == {
            name: (0, "") for name in answered
        }
        assert {name: len(cli_answer.lines()) for name, cli_answer in answered.items()} == {
            name: sum(1 for guarded in guards.values() if guarded <= opened[name]) for name in answered
        }
        assert frozenset().union(*guards.values()) <= frozenset().union(*opened.values())
        assert {
            name: sorted(path.relative_to(tmp_path / name).as_posix() for path in (tmp_path / name).rglob("*") if path.is_file())
            for name in answered
        } == {name: sorted(cli_answer.lines()) for name, cli_answer in answered.items()}
