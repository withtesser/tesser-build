from __future__ import annotations

import os
import subprocess
import sys

import srv.cli as cli


class TestCliHost:

    def test_add_runs_the_add_command(self, postgres_dsn: str) -> None:
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path), "ALPHA_STORAGE": postgres_dsn, "BETA_KEY": "a", "RESTATE_URL": "http://engine.invalid:8080"}
        added = subprocess.run(
            [sys.executable, "-m", cli.CliHost.__module__, "add", "a", "p"],
            capture_output=True, text=True, check=False, env=env,
        )
        assert added.returncode == 0, added.stderr

    def test_a_missing_argument_or_command_exits_two_with_the_usage(self, postgres_dsn: str) -> None:
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path), "ALPHA_STORAGE": postgres_dsn, "BETA_KEY": "a", "RESTATE_URL": "http://engine.invalid:8080"}
        missing_argument = subprocess.run(
            [sys.executable, "-m", cli.CliHost.__module__, "add", "a"],
            capture_output=True, text=True, check=False, env=env,
        )
        missing_command = subprocess.run(
            [sys.executable, "-m", cli.CliHost.__module__, "a", "p"],
            capture_output=True, text=True, check=False, env=env,
        )
        assert [missing_argument.returncode, missing_command.returncode] == [2, 2]
        assert "usage: add <name> <part>" in missing_argument.stdout
        assert "usage: add <name> <part> | create <name> | approve <name> | find <name>" in missing_command.stdout

    def test_an_unexpected_failure_exits_one_and_leaks_nothing_to_stdout(self) -> None:
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path), "ALPHA_STORAGE": "bogus", "BETA_KEY": "a", "RESTATE_URL": "http://engine.invalid:8080"}
        failed = subprocess.run(
            [sys.executable, "-m", cli.CliHost.__module__, "add", "a", "p"],
            capture_output=True, text=True, check=False, env=env,
        )
        assert failed.returncode == 1
        assert failed.stdout == "unexpected error\n"
        assert "unknown_backend" in failed.stderr
