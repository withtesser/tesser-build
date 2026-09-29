from __future__ import annotations

import os
import pathlib
import subprocess
import sys


class TestGenerateHost:

    def test_the_voice_spec_generates_and_exits_zero_listing_what_it_wrote(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.generate", str(tree / "specs" / "voice.toml"), str(tmp_path / "voice")],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert completed.returncode == 0, completed.stderr
        assert "calls/domain/call.py" in completed.stdout.splitlines()
        assert (tmp_path / "voice" / "calls" / "domain" / "call.py").is_file()

    def test_a_file_it_would_write_differently_exits_one_on_stderr(self, tmp_path: pathlib.Path) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "voice").mkdir()
        (tmp_path / "voice" / ".tesser-root").write_text("ungated\n")

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.generate", str(tree / "specs" / "voice.toml"), str(tmp_path / "voice")],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert completed.returncode == 1
        assert completed.stderr == (
            "generate: the output directory already has .tesser-root, which the generator would write differently\n"
        )

    def test_a_directory_holding_only_files_it_does_not_write_generates_beside_them(
        self, tmp_path: pathlib.Path
    ) -> None:
        tree = pathlib.Path(__file__).resolve().parents[2]
        (tmp_path / "voice").mkdir()
        (tmp_path / "voice" / "README.md").write_text("# voice\n")

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.generate", str(tree / "specs" / "voice.toml"), str(tmp_path / "voice")],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert (completed.returncode, (tmp_path / "voice" / "README.md").read_text()) == (0, "# voice\n"), completed.stderr
        assert (tmp_path / "voice" / "calls" / "domain" / "call.py").is_file()

    def test_a_missing_argument_exits_two_with_the_usage(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.generate"],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        )

        assert completed.returncode == 2
        assert "usage: python -m srv.cli.generate" in completed.stderr
