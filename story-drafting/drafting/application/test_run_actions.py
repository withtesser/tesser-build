from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self) -> None:
        self.saved: list[ports.SaveRunRequest] = []

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self.saved.append(save_run_request)
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.NOT_FOUND, runs=())


@ts.fake
class FakeRunStore(ports.RunStore):

    def __init__(self, fake_run_repository: FakeRunRepository) -> None:
        self._fake_run_repository = fake_run_repository

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield self._fake_run_repository


class TestRunActions:

    async def test_recording_a_run_saves_it_whole_once_and_answers_its_id(self) -> None:
        fake_run_repository = FakeRunRepository()
        run = domain.Run(
            domain.RunSpec(
                run_id="r1", job="ship", stage="awaiting_pick", stories=(domain.StorySpec(text="a story"),), accepted_stories=()
            )
        )
        record_run_response = await application.RunActions(FakeRunStore(fake_run_repository)).record_run(
            relays.RecordRunRequest(run=run)
        )
        assert record_run_response.run_id == "r1"
        assert [
            (saved.run_id, saved.job, saved.stage, saved.stories, saved.accepted_stories)
            for saved in fake_run_repository.saved
        ] == [("r1", "ship", "awaiting_pick", ("a story",), ())]
