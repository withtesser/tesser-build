from __future__ import annotations

import pathlib

import tesser.testing as ts


class TestGenerateHost:

    def test_the_voice_spec_generates_and_exits_zero_listing_what_it_wrote(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        cli = ts.Cli("srv.cli.generate")

        cli_answer = cli.run(str(tree / "specs" / "voice.toml"), str(tmp_path / "voice"))

        assert cli_answer.exit_code == 0, cli_answer.stderr
        assert "calls/domain/call.py" in cli_answer.lines()
        assert (tmp_path / "voice" / "calls" / "domain" / "call.py").is_file()

    def test_a_file_it_would_write_differently_exits_one_on_stderr(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "voice").mkdir()
        (tmp_path / "voice" / ".tesser-root").write_text("ungated\n")
        cli = ts.Cli("srv.cli.generate")

        cli_answer = cli.run(str(tree / "specs" / "voice.toml"), str(tmp_path / "voice"))

        assert cli_answer.exit_code == 1
        assert cli_answer.stderr == (
            "generate: the output directory already has .tesser-root, which the generator would write differently\n"
        )

    def test_a_directory_holding_only_files_it_does_not_write_generates_beside_them(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "voice").mkdir()
        (tmp_path / "voice" / "README.md").write_text("# voice\n")
        cli = ts.Cli("srv.cli.generate")

        cli_answer = cli.run(str(tree / "specs" / "voice.toml"), str(tmp_path / "voice"))

        assert (cli_answer.exit_code, (tmp_path / "voice" / "README.md").read_text()) == (0, "# voice\n"), cli_answer.stderr
        assert (tmp_path / "voice" / "calls" / "domain" / "call.py").is_file()

    def test_a_missing_argument_exits_two_with_the_usage(self) -> None:
        cli = ts.Cli("srv.cli.generate")

        cli_answer = cli.run()

        assert cli_answer.exit_code == 2
        assert "usage: python -m srv.cli.generate" in cli_answer.stderr
