import os
import uuid

import pytest

import tesser.testing.host as host


def test_a_cli_run_answers_with_the_hosts_exit_code_and_output() -> None:
    cli = host.Cli("platform")  # tesser:debt TB085
    cli_answer = cli.run()

    assert cli_answer.exit_code == 0
    assert cli_answer.lines() != ()
    assert cli_answer.stderr == ""


def test_a_cli_run_passes_its_arguments_and_reports_a_failing_exit() -> None:
    cli = host.Cli("json.tool")  # tesser:debt TB085
    cli_answer = cli.run("no-such-file-" + str(uuid.uuid4()))

    assert cli_answer.exit_code != 0
    assert cli_answer.stdout == ""
    assert "no-such-file-" in cli_answer.stderr


def test_a_cli_host_sees_the_callers_import_path() -> None:
    cli = host.Cli("tesser.testing.host")  # tesser:debt TB085
    cli_answer = cli.run()

    assert cli_answer.exit_code == 0


def test_served_reads_the_address_the_runner_named() -> None:
    assert host.served("PATH") == os.environ["PATH"]


def test_served_refuses_a_variable_the_runner_did_not_set() -> None:
    variable = "TESSER_UNSET_" + uuid.uuid4().hex.upper()

    with pytest.raises(LookupError, match=variable):
        host.served(variable)
