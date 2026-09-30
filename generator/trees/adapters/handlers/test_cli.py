from __future__ import annotations

import pytest

import tesser.testing as ts

import protocol
import trees.adapters.handlers as handlers
import trees.client as client


@ts.fake
class FakeTreesClient(client.TreesClient):

    def __init__(
        self,
        problems: tuple[str, ...] = (),
        paths: tuple[str, ...] = ("calls/domain/call.py",),
        printed: tuple[client.PrintedFile, ...] = (),
    ) -> None:
        self._problems = problems
        self._paths = paths
        self._printed = printed
        self.asked: list[client.GenerateTreeRequest] = []

    def generate_tree(self, generate_tree_request: client.GenerateTreeRequest) -> client.GenerateTreeResponse:
        self.asked.append(generate_tree_request)
        return client.GenerateTreeResponse(problems=self._problems, paths=self._paths, printed=self._printed)


class TestHandler:

    def test_a_generated_tree_exits_zero_and_lists_its_paths(self) -> None:
        fake_trees_client = FakeTreesClient(paths=(".tesser-root", "calls/domain/call.py"))

        cli_response = handlers.Handler(fake_trees_client).generate(
            protocol.CliRequest(args=("specs/voice.toml", "/tmp/voice"))
        )

        assert cli_response == protocol.CliResponse(0, stdout=".tesser-root\ncalls/domain/call.py", stderr="")
        assert [
            (generate_tree_request.spec_path, generate_tree_request.out_dir, generate_tree_request.printed)
            for generate_tree_request in fake_trees_client.asked
        ] == [("specs/voice.toml", "/tmp/voice", ())]

    def test_each_printed_path_is_asked_for_and_follows_the_paths_under_its_header(self) -> None:
        fake_trees_client = FakeTreesClient(
            paths=("calls/domain/call.py", "tests/test_acceptance.py"),
            printed=(
                client.PrintedFile(path="tests/test_acceptance.py", text="class TestPlacingCalls:\n    pass\n"),
                client.PrintedFile(path="calls/domain/call.py", text="class Call:\n"),
            ),
        )

        cli_response = handlers.Handler(fake_trees_client).generate(
            protocol.CliRequest(
                args=("specs/voice.toml", "/tmp/voice", "--print", "tests/test_acceptance.py", "--print", "calls/domain/call.py")
            )
        )

        assert cli_response == protocol.CliResponse(
            0,
            stdout=(
                "calls/domain/call.py\ntests/test_acceptance.py\n"
                "\n--- tests/test_acceptance.py\nclass TestPlacingCalls:\n    pass\n"
                "\n--- calls/domain/call.py\nclass Call:"
            ),
            stderr="",
        )
        assert [generate_tree_request.printed for generate_tree_request in fake_trees_client.asked] == [
            ("tests/test_acceptance.py", "calls/domain/call.py")
        ]

    def test_problems_exit_one_on_stderr_with_the_generate_prefix(self) -> None:
        handler = handlers.Handler(FakeTreesClient(problems=("first thing", "second thing"), paths=()))

        cli_response = handler.generate(protocol.CliRequest(args=("spec.toml", "out")))

        assert cli_response == protocol.CliResponse(
            1, stdout="", stderr="generate: first thing\ngenerate: second thing"
        )

    def test_a_missing_output_directory_argument_is_a_usage_error(self) -> None:
        with pytest.raises(protocol.UsageError):
            handlers.Handler(FakeTreesClient()).generate(protocol.CliRequest(args=("spec.toml",)))

    def test_a_print_without_a_path_is_a_usage_error(self) -> None:
        with pytest.raises(protocol.UsageError) as raised:
            handlers.Handler(FakeTreesClient()).generate(protocol.CliRequest(args=("spec.toml", "out", "--print")))
        assert "[--print <path>]..." in str(raised.value)

    def test_an_unknown_option_is_a_usage_error(self) -> None:
        with pytest.raises(protocol.UsageError) as raised:
            handlers.Handler(FakeTreesClient()).generate(protocol.CliRequest(args=("spec.toml", "out", "--verbose")))
        assert "unknown option --verbose" in str(raised.value)

    def test_an_extra_argument_is_a_usage_error(self) -> None:
        with pytest.raises(protocol.UsageError):
            handlers.Handler(FakeTreesClient()).generate(protocol.CliRequest(args=("spec.toml", "out", "extra")))
