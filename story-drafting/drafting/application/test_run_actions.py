from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self, runs: dict[str, ports.Run]) -> None:
        self._runs = runs

    async def issue_run_id(self, issue_run_id_request: ports.IssueRunIdRequest) -> ports.IssueRunIdResponse:
        return ports.IssueRunIdResponse(run_id="issued-1")

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self._runs[save_run_request.run_id] = ports.Run(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            step=save_run_request.step,
            drafted_stories=save_run_request.drafted_stories,
            accepted_stories=save_run_request.accepted_stories,
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        if load_run_request.run_id not in self._runs:
            return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.NOT_FOUND, runs=())
        return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.FOUND, runs=(self._runs[load_run_request.run_id],))


@ts.fake
class FakeRunStore(ports.RunStore):

    def __init__(self) -> None:
        self.runs: dict[str, ports.Run] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield FakeRunRepository(self.runs)


class TestRunActions:

    async def test_recording_a_run_saves_it_whole_under_its_run_id(self) -> None:
        fake_run_store = FakeRunStore()

        await application.RunActions(fake_run_store).record_run(
            relays.RecordRunRequest(
                run_id="r7",
                job="ship a release",
                step="awaiting_pick",
                drafted_stories=("first", "second"),
                accepted_stories=(),
            )
        )

        assert fake_run_store.runs["r7"] == ports.Run(
            run_id="r7",
            job="ship a release",
            step="awaiting_pick",
            drafted_stories=("first", "second"),
            accepted_stories=(),
        )

    async def test_recording_a_run_answers_the_run_id_it_saved(self) -> None:
        record_run_response = await application.RunActions(FakeRunStore()).record_run(
            relays.RecordRunRequest(
                run_id="r7",
                job="ship a release",
                step="awaiting_pick",
                drafted_stories=("first", "second"),
                accepted_stories=(),
            )
        )

        assert record_run_response.run_id == "r7"
