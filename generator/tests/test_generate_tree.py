from __future__ import annotations

import pathlib

import tesser.testing as ts


class TestGeneratingTrees:

    def test_every_committed_spec_generates_every_template_and_exits_zero(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[1]
        template_count = len(list((tree / "templates").rglob("*.tmpl")))
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
            name: template_count for name in answered
        }
        assert {
            name: sorted(path.relative_to(tmp_path / name).as_posix() for path in (tmp_path / name).rglob("*") if path.is_file())
            for name in answered
        } == {name: sorted(cli_answer.lines()) for name, cli_answer in answered.items()}
