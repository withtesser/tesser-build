from __future__ import annotations

import pytest
import tesser.testing as ts

import protocol
import tessercheck.adapters.handlers as handlers
import tessercheck.client as client


@ts.fake
class FakeCheckClient(client.TessercheckClient):
    def __init__(self, *findings: str) -> None:
        self.findings = findings
        self.roots: list[str] = []
        self.fixes: list[str] = []

    def check_tree(self, check_tree_request: client.CheckTreeRequest) -> client.CheckTreeResponse:
        self.roots.append(check_tree_request.tree)
        return client.CheckTreeResponse(findings=self.findings)

    def check_file(self, check_file_request: client.CheckFileRequest) -> client.CheckFileResponse:
        self.roots.append(check_file_request.tree)
        return client.CheckFileResponse(governance="governed", findings=self.findings, codes=())

    def check_write(self, check_write_request: client.CheckWriteRequest) -> client.CheckWriteResponse:
        self.roots.append(check_write_request.tree)
        return client.CheckWriteResponse(
            governance="governed", mode="advisory", action="advise", findings=self.findings, codes=()
        )

    def mark_debt(self, mark_debt_request: client.MarkDebtRequest) -> client.MarkDebtResponse:
        self.roots.append(mark_debt_request.tree)
        return client.MarkDebtResponse(files=0, remaining=self.findings)

    def apply_renames(self, apply_renames_request: client.ApplyRenamesRequest) -> client.ApplyRenamesResponse:
        self.roots.append(apply_renames_request.tree)
        return client.ApplyRenamesResponse(files=0, remaining=self.findings)

    def fix_tree(self, fix_tree_request: client.FixTreeRequest) -> client.FixTreeResponse:
        self.fixes.append(fix_tree_request.tree)
        return client.FixTreeResponse(
            files=1, fixed=("a.py:3: TB085 a.f names made for a tag",), remaining=self.findings
        )

    def render_rulebook(self, render_rulebook_request: client.RenderRulebookRequest) -> client.RenderRulebookResponse:
        self.roots.append(render_rulebook_request.tree)
        return client.RenderRulebookResponse(rendered="| rendered |")


@ts.fake
class FakeRulebookNotRenderedClient(client.TessercheckClient):

    def check_tree(self, check_tree_request: client.CheckTreeRequest) -> client.CheckTreeResponse:
        raise client.RulebookNotRendered("rulebook_unreadable", "checks.py cannot be read")

    def check_file(self, check_file_request: client.CheckFileRequest) -> client.CheckFileResponse:
        raise client.RulebookNotRendered("rulebook_unreadable", "checks.py cannot be read")

    def check_write(self, check_write_request: client.CheckWriteRequest) -> client.CheckWriteResponse:
        raise client.RulebookNotRendered("rulebook_unreadable", "checks.py cannot be read")

    def mark_debt(self, mark_debt_request: client.MarkDebtRequest) -> client.MarkDebtResponse:
        raise client.RulebookNotRendered("rulebook_unreadable", "checks.py cannot be read")

    def apply_renames(self, apply_renames_request: client.ApplyRenamesRequest) -> client.ApplyRenamesResponse:
        raise client.RulebookNotRendered("rulebook_unreadable", "checks.py cannot be read")

    def fix_tree(self, fix_tree_request: client.FixTreeRequest) -> client.FixTreeResponse:
        raise client.RulebookNotRendered("rulebook_unreadable", "checks.py cannot be read")

    def render_rulebook(self, render_rulebook_request: client.RenderRulebookRequest) -> client.RenderRulebookResponse:
        raise client.RulebookNotRendered("rulebook_unreadable", "checks.py cannot be read")


def test_a_rulebook_not_rendered_exits_two_with_the_context_s_message() -> None:
    cli_response = handlers.Handler(FakeRulebookNotRenderedClient()).rulebook(protocol.CliRequest(("tree",)))
    assert cli_response == protocol.CliResponse(2, stdout="", stderr="checks.py cannot be read")


def test_the_tree_argument_reaches_the_client() -> None:
    fake_check_client = FakeCheckClient()
    cli_response = handlers.Handler(fake_check_client).check(protocol.CliRequest(("some/tree",)))
    assert fake_check_client.roots == ["some/tree"]
    assert cli_response.exit_code == 0


def test_no_argument_checks_the_working_directory() -> None:
    fake_check_client = FakeCheckClient()
    handlers.Handler(fake_check_client).check(protocol.CliRequest(()))
    assert fake_check_client.roots == ["."]


def test_findings_become_lines_and_a_failing_exit_code() -> None:
    fake_check_client = FakeCheckClient("a.py:1: TB040 one", "b.py:2: TB041 two")
    cli_response = handlers.Handler(fake_check_client).check(protocol.CliRequest(("tree",)))
    assert cli_response.exit_code == 1
    assert cli_response.stdout == "a.py:1: TB040 one\nb.py:2: TB041 two"
    assert cli_response.stderr == ""


def test_a_clean_tree_prints_nothing_and_exits_zero() -> None:
    cli_response = handlers.Handler(FakeCheckClient()).check(protocol.CliRequest(("tree",)))
    assert cli_response.exit_code == 0
    assert cli_response.stdout == ""


def test_an_extra_argument_is_a_usage_error() -> None:
    fake_check_client = FakeCheckClient()
    with pytest.raises(protocol.UsageError):
        handlers.Handler(fake_check_client).check(protocol.CliRequest(("tree", "surplus")))
    assert fake_check_client.roots == []


def test_a_check_without_the_fix_flag_never_reaches_the_fix() -> None:
    fake_check_client = FakeCheckClient("a.py:1: TB040 one")
    handlers.Handler(fake_check_client).check(protocol.CliRequest(("tree",)))
    assert fake_check_client.fixes == []
    assert fake_check_client.roots == ["tree"]


def test_the_fix_flag_sends_the_tree_to_the_fix_and_not_to_the_check() -> None:
    fake_check_client = FakeCheckClient()
    handlers.Handler(fake_check_client).check(protocol.CliRequest(("--fix", "some/tree")))
    assert fake_check_client.fixes == ["some/tree"]
    assert fake_check_client.roots == []


def test_the_fix_flag_may_follow_the_tree() -> None:
    fake_check_client = FakeCheckClient()
    handlers.Handler(fake_check_client).check(protocol.CliRequest(("some/tree", "--fix")))
    assert fake_check_client.fixes == ["some/tree"]


def test_the_fix_flag_alone_fixes_the_working_directory() -> None:
    fake_check_client = FakeCheckClient()
    handlers.Handler(fake_check_client).check(protocol.CliRequest(("--fix",)))
    assert fake_check_client.fixes == ["."]


def test_a_fix_that_leaves_nothing_reports_what_it_fixed_and_exits_zero() -> None:
    cli_response = handlers.Handler(FakeCheckClient()).check(protocol.CliRequest(("--fix", "tree")))
    assert cli_response.exit_code == 0
    assert cli_response.stdout == (
        "fixed 1 finding(s), rewriting 1 file(s)\n"
        "fixed: a.py:3: TB085 a.f names made for a tag"
    )
    assert cli_response.stderr == ""


def test_what_a_fix_leaves_becomes_finding_lines_and_a_failing_exit_code() -> None:
    fake_check_client = FakeCheckClient("b.py:2: TB071 two")
    cli_response = handlers.Handler(fake_check_client).check(protocol.CliRequest(("--fix", "tree")))
    assert cli_response.exit_code == 1
    assert cli_response.stdout == (
        "fixed 1 finding(s), rewriting 1 file(s)\n"
        "fixed: a.py:3: TB085 a.f names made for a tag\n"
        "1 finding(s) remain:\n"
        "b.py:2: TB071 two"
    )


def test_an_extra_argument_beside_the_fix_flag_is_a_usage_error() -> None:
    fake_check_client = FakeCheckClient()
    with pytest.raises(protocol.UsageError):
        handlers.Handler(fake_check_client).check(protocol.CliRequest(("--fix", "tree", "surplus")))
    assert fake_check_client.fixes == []


def test_the_tree_argument_reaches_the_client_on_a_mark() -> None:
    fake_check_client = FakeCheckClient()
    cli_response = handlers.Handler(fake_check_client).mark(protocol.CliRequest(("some/tree",)))
    assert fake_check_client.roots == ["some/tree"]
    assert cli_response.exit_code == 0
    assert cli_response.stdout == "marked 0 file(s)"
    assert cli_response.stderr == ""


def test_no_argument_marks_the_working_directory() -> None:
    fake_check_client = FakeCheckClient()
    handlers.Handler(fake_check_client).mark(protocol.CliRequest(()))
    assert fake_check_client.roots == ["."]


def test_what_a_mark_cannot_write_becomes_lines_and_a_failing_exit_code() -> None:
    fake_check_client = FakeCheckClient("a.py:1: TB044 one", "b.py:2: TB045 two")
    cli_response = handlers.Handler(fake_check_client).mark(protocol.CliRequest(("tree",)))
    assert cli_response.exit_code == 1
    assert cli_response.stdout == (
        "marked 0 file(s)\n"
        "2 finding(s) this cannot mark:\n"
        "a.py:1: TB044 one\n"
        "b.py:2: TB045 two"
    )
    assert cli_response.stderr == ""


def test_an_extra_argument_to_mark_is_a_usage_error() -> None:
    fake_check_client = FakeCheckClient()
    with pytest.raises(protocol.UsageError):
        handlers.Handler(fake_check_client).mark(protocol.CliRequest(("tree", "surplus")))
