from __future__ import annotations

import pytest

import protocol


def test_an_argument_at_its_index_comes_back() -> None:
    cli_request = protocol.CliRequest(args=("/repo", "--verbose"))
    assert cli_request.arg(0, "repo-root", "usage: prog <repo-root>") == "/repo"
    assert cli_request.arg(1, "flag", "usage: prog <repo-root>") == "--verbose"


def test_a_missing_argument_names_itself_and_carries_the_usage() -> None:
    with pytest.raises(protocol.UsageError) as raised:
        protocol.CliRequest(args=()).arg(0, "repo-root", "usage: prog <repo-root>")
    assert "missing argument <repo-root>" in str(raised.value)
    assert "usage: prog <repo-root>" in str(raised.value)


def test_an_empty_argument_is_a_missing_argument() -> None:
    with pytest.raises(protocol.UsageError) as raised:
        protocol.CliRequest(args=("",)).arg(0, "repo-root", "usage: prog <repo-root>")
    assert "missing argument <repo-root>" in str(raised.value)


def test_an_argument_past_the_end_is_a_missing_argument() -> None:
    with pytest.raises(protocol.UsageError):
        protocol.CliRequest(args=("/repo",)).arg(1, "second", "usage: prog <repo-root>")


def test_the_exact_argument_count_passes_the_extra_argument_gate() -> None:
    cli_request = protocol.CliRequest(args=("/repo",))
    cli_request.no_extra_args(1, "usage: prog")
    assert cli_request.arg(0, "repo-root", "usage: prog") == "/repo"


def test_fewer_arguments_than_the_count_pass_the_extra_argument_gate() -> None:
    cli_request = protocol.CliRequest(args=())
    cli_request.no_extra_args(1, "usage: prog")
    assert cli_request.args == ()


def test_an_extra_argument_is_rejected_with_the_usage() -> None:
    with pytest.raises(protocol.UsageError) as raised:
        protocol.CliRequest(args=("/repo", "extra")).no_extra_args(1, "usage: prog <repo-root>")
    assert "unexpected extra arguments" in str(raised.value)
    assert "usage: prog <repo-root>" in str(raised.value)


def test_an_option_takes_the_value_after_each_of_its_flags_in_order() -> None:
    cli_request = protocol.CliRequest(args=("--print", "a.py", "spec.toml", "--print", "b.py", "out"))

    rest, values = cli_request.take_option("--print", "path", "usage: prog")

    assert (rest, values) == (protocol.CliRequest(args=("spec.toml", "out")), ("a.py", "b.py"))


def test_a_listed_option_takes_every_value_after_it_once_the_positional_arguments_are_in() -> None:
    cli_request = protocol.CliRequest(args=("--print", "a.py", "spec.toml", "out", "--print", "b.py", "c.py", "--print", "d.py"))

    rest, values = cli_request.take_listed_option("--print", "path", "usage: prog", 2)

    assert (rest, values) == (protocol.CliRequest(args=("spec.toml", "out")), ("a.py", "b.py", "c.py", "d.py"))


def test_a_listed_option_before_the_positional_arguments_takes_one_value() -> None:
    cli_request = protocol.CliRequest(args=("--print", "a.py", "spec.toml", "out", "extra"))

    rest, values = cli_request.take_listed_option("--print", "path", "usage: prog", 2)

    assert (rest, values) == (protocol.CliRequest(args=("spec.toml", "out", "extra")), ("a.py",))


def test_an_absent_option_takes_nothing_and_leaves_the_arguments() -> None:
    cli_request = protocol.CliRequest(args=("spec.toml", "out"))

    assert cli_request.take_option("--print", "path", "usage: prog") == (cli_request, ())


def test_an_option_without_a_value_names_its_value_and_carries_the_usage() -> None:
    with pytest.raises(protocol.UsageError) as raised:
        protocol.CliRequest(args=("spec.toml", "out", "--print")).take_option("--print", "path", "usage: prog")
    assert "missing <path> after --print" in str(raised.value)
    assert "usage: prog" in str(raised.value)


def test_an_option_followed_by_another_option_has_no_value() -> None:
    with pytest.raises(protocol.UsageError) as raised:
        protocol.CliRequest(args=("--print", "--print", "a.py")).take_option("--print", "path", "usage: prog")
    assert "missing <path> after --print" in str(raised.value)


def test_arguments_without_options_pass_the_option_gate() -> None:
    cli_request = protocol.CliRequest(args=("spec.toml", "-"))
    cli_request.no_options("usage: prog")
    assert cli_request.args == ("spec.toml", "-")


def test_an_unknown_option_is_rejected_with_the_usage() -> None:
    with pytest.raises(protocol.UsageError) as raised:
        protocol.CliRequest(args=("spec.toml", "--verbose")).no_options("usage: prog")
    assert "unknown option --verbose" in str(raised.value)
    assert "usage: prog" in str(raised.value)


def test_ok_is_exit_zero_on_stdout_with_an_empty_stderr() -> None:
    cli_response = protocol.CliResponse.ok("done")
    assert cli_response.exit_code == 0
    assert cli_response.stdout == "done"
    assert cli_response.stderr == ""


def test_a_response_carries_the_exit_code_and_both_streams() -> None:
    cli_response = protocol.CliResponse(2, stdout="", stderr="boom")
    assert cli_response.exit_code == 2
    assert cli_response.stdout == ""
    assert cli_response.stderr == "boom"


def test_two_responses_with_the_same_fields_are_equal() -> None:
    assert protocol.CliResponse.ok("done") == protocol.CliResponse(0, stdout="done", stderr="")
    assert protocol.CliResponse.ok("done") != protocol.CliResponse(1, stdout="done", stderr="")


def test_a_request_holds_its_arguments_as_given() -> None:
    assert protocol.CliRequest(args=("a", "b")).args == ("a", "b")
    assert protocol.CliRequest(args=("a", "b")) == protocol.CliRequest(args=("a", "b"))
