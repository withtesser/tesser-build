from __future__ import annotations

import pytest

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import tesser.errors as errors


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self) -> None:
        self.saved: list[tuple[str, str, str, tuple[str, ...]]] = []

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self.saved.append(
            (save_run_request.run_id, save_run_request.job, save_run_request.stage, save_run_request.stories)
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def get_run(self, get_run_request: ports.GetRunRequest) -> ports.GetRunResponse:
        return ports.GetRunResponse(outcome=ports.GetRunOutcome.NOT_FOUND, runs=())


class TestRunActions:

    async def test_keeping_saves_the_run_once_as_drafting_and_answers_its_id(self) -> None:
        fake_run_repository = FakeRunRepository()
        keep_run_response = await application.RunActions(fake_run_repository).keep_run(
            relays.KeepRunRequest(run_id="r1", job="a job")
        )
        assert keep_run_response.run_id == "r1"
        assert fake_run_repository.saved == [("r1", "a job", "drafting", ())]

    async def test_offering_stories_saves_the_run_once_awaiting_the_pick_with_them(self) -> None:
        fake_run_repository = FakeRunRepository()
        offer_stories_response = await application.RunActions(fake_run_repository).offer_stories(
            relays.OfferStoriesRequest(run_id="r1", job="a job", stories=("a story", "another story"))
        )
        assert offer_stories_response.run_id == "r1"
        assert fake_run_repository.saved == [("r1", "a job", "awaiting_pick", ("a story", "another story"))]

    async def test_offering_no_stories_is_refused_and_saves_nothing(self) -> None:
        fake_run_repository = FakeRunRepository()
        with pytest.raises(errors.DomainError):
            await application.RunActions(fake_run_repository).offer_stories(
                relays.OfferStoriesRequest(run_id="r1", job="a job", stories=())
            )
        assert fake_run_repository.saved == []
