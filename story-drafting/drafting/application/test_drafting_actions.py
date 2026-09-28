from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeDraftingRepository(ports.DraftingRepository):

    def __init__(self) -> None:
        self.saved: list[ports.DraftingRow] = []

    async def issue_drafting_id(
        self, issue_drafting_id_request: ports.IssueDraftingIdRequest
    ) -> ports.IssueDraftingIdResponse:
        return ports.IssueDraftingIdResponse(drafting_id="issued-1")

    async def save_drafting(self, save_drafting_request: ports.SaveDraftingRequest) -> ports.SaveDraftingResponse:
        self.saved.append(save_drafting_request.drafting_row)
        return ports.SaveDraftingResponse(drafting_id=save_drafting_request.drafting_row.drafting_id)

    async def load_drafting(self, load_drafting_request: ports.LoadDraftingRequest) -> ports.LoadDraftingResponse:
        return ports.LoadDraftingResponse(outcome=ports.LoadDraftingOutcome.NOT_FOUND, drafting_rows=())


@ts.fake
class FakeDraftingStore(ports.DraftingStore):

    def __init__(self, fake_drafting_repository: FakeDraftingRepository) -> None:
        self._fake_drafting_repository = fake_drafting_repository

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.DraftingRepository]:
        yield self._fake_drafting_repository


class TestDraftingActions:

    async def test_keeping_saves_the_drafting_once_awaiting_the_pick_with_its_stories_and_none_accepted(self) -> None:
        fake_drafting_repository = FakeDraftingRepository()

        keep_drafted_stories_response = await application.DraftingActions(
            FakeDraftingStore(fake_drafting_repository)
        ).keep_drafted_stories(relays.KeepDraftedStoriesRequest(drafting_id="d1", job="a job", texts=("first", "second")))

        assert keep_drafted_stories_response.drafting_id == "d1"
        assert [
            (
                drafting_row.drafting_id,
                drafting_row.job,
                drafting_row.step,
                [(story_row.story_id, story_row.text) for story_row in drafting_row.stories],
                drafting_row.accepted_stories,
            )
            for drafting_row in fake_drafting_repository.saved
        ] == [("d1", "a job", "awaiting_pick", [("1", "first"), ("2", "second")], ())]
