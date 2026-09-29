from __future__ import annotations

import pytest

import tesser.testing as ts

import protocol
import rendering.adapters.handlers as handlers
import rendering.client as client


@ts.fake
class FakeRenderingClient(client.RenderingClient):

    def __init__(self, problems: tuple[str, ...], written: tuple[str, ...], kept: tuple[str, ...]) -> None:
        self._problems = problems
        self._written = written
        self._kept = kept
        self.asked: list[client.RenderCompositionRequest] = []
        self.checked: list[client.CheckCompositionRequest] = []

    def render_composition(self, render_composition_request: client.RenderCompositionRequest) -> client.RenderCompositionResponse:
        self.asked.append(render_composition_request)
        return client.RenderCompositionResponse(problems=self._problems, written=self._written, kept=self._kept)

    def check_composition(self, check_composition_request: client.CheckCompositionRequest) -> client.CheckCompositionResponse:
        self.checked.append(check_composition_request)
        return client.CheckCompositionResponse(problems=self._problems, drifted=self._written, checked=len(self._kept))


class TestHandler:

    def test_a_rendered_tree_exits_zero_and_lists_what_it_wrote_then_what_it_kept(self) -> None:
        fake_rendering_client = FakeRenderingClient(problems=(), written=(".tesser-root", "lending/client/client.py"), kept=("lending/domain/loan.py",))

        cli_response = handlers.Handler(fake_rendering_client).render(protocol.CliRequest(args=("compositions/lending", "/tmp/lending")))

        assert cli_response == protocol.CliResponse(
            0, stdout=".tesser-root\nlending/client/client.py\nkept lending/domain/loan.py", stderr=""
        )
        assert [(asked.composition_dir, asked.out_dir) for asked in fake_rendering_client.asked] == [
            ("compositions/lending", "/tmp/lending")
        ]

    def test_problems_exit_one_each_on_its_own_line(self) -> None:
        fake_rendering_client = FakeRenderingClient(problems=("the output directory is a file", "a spec lacks the key app"), written=(), kept=())

        cli_response = handlers.Handler(fake_rendering_client).render(protocol.CliRequest(args=("compositions/lending", "/tmp/lending")))

        assert cli_response == protocol.CliResponse(
            1, stdout="", stderr="render: the output directory is a file\nrender: a spec lacks the key app"
        )

    def test_a_missing_output_directory_is_a_usage_error_that_asks_nothing(self) -> None:
        fake_rendering_client = FakeRenderingClient(problems=(), written=(), kept=())

        with pytest.raises(protocol.UsageError):
            handlers.Handler(fake_rendering_client).render(protocol.CliRequest(args=("compositions/lending",)))

        assert fake_rendering_client.asked == []

    def test_a_check_that_finds_no_drift_exits_zero_and_says_how_many_files_match(self) -> None:
        fake_rendering_client = FakeRenderingClient(problems=(), written=(), kept=("a", "b"))

        cli_response = handlers.Handler(fake_rendering_client).check(protocol.CliRequest(args=("compositions/lending", "/tmp/lending")))

        assert cli_response == protocol.CliResponse(0, stdout="check: 2 rendered files match compositions/lending", stderr="")
        assert [(asked.composition_dir, asked.tree_dir) for asked in fake_rendering_client.checked] == [
            ("compositions/lending", "/tmp/lending")
        ]

    def test_a_check_that_finds_drift_exits_one_naming_each_path(self) -> None:
        fake_rendering_client = FakeRenderingClient(
            problems=(), written=("loans/client/client.py differs from what the composition renders",), kept=()
        )

        cli_response = handlers.Handler(fake_rendering_client).check(protocol.CliRequest(args=("compositions/lending", "/tmp/lending")))

        assert cli_response == protocol.CliResponse(
            1, stdout="", stderr="check: loans/client/client.py differs from what the composition renders"
        )
