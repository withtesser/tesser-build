from __future__ import annotations

import os

import pytest

import srv.cli as cli


class TestCliHost:

    def test_get_call_for_a_call_that_was_never_placed_exits_one_with_the_contexts_wording(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = cli.CliHost().run(["get-call", "cli-never-placed"])

        assert exit_code == 1
        assert capsys.readouterr().out == "no call 'cli-never-placed'\n"

    def test_an_unknown_command_or_a_missing_argument_exits_two_with_the_usage(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_codes = [cli.CliHost().run([]), cli.CliHost().run(["hang-up"]), cli.CliHost().run(["get-call"])]
        printed = capsys.readouterr().out

        assert exit_codes == [2, 2, 2]
        assert printed.count("usage: place-call | get-call <call_id>\n") == 2
        assert "missing argument <call_id>\nusage: get-call <call_id>\n" in printed

    def test_an_unexpected_failure_exits_one_and_leaks_nothing_to_stdout(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ambient_storage = os.environ["CALLS_STORAGE"]
        del os.environ["CALLS_STORAGE"]
        try:
            exit_code = cli.CliHost().run(["get-call", "c7"])
        finally:
            os.environ.update(CALLS_STORAGE=ambient_storage)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert captured.out == "unexpected error\n"
        assert "CALLS_STORAGE is required" in captured.err
