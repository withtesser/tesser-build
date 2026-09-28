from __future__ import annotations

import contextlib
import typing

import pytest

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client


@ts.fake
class FakeDraftingOrchestratorRelay(relays.DraftingOrchestratorRelay):

    def __init__(self) -> None:
        self.started: list[relays.ConductDraftingRequest] = []

    async def start_conduct_drafting(
        self, conduct_drafting_request: relays.ConductDraftingRequest
    ) -> relays.StartConductDraftingResponse:
        self.started.append(conduct_drafting_request)
        return relays.StartConductDraftingResponse(drafting_id=conduct_drafting_request.drafting_id)


@ts.fake
class FakeDraftingRepository(ports.DraftingRepository):

    def __init__(self, drafting_rows: dict[str, ports.DraftingRow]) -> None:
        self._drafting_rows = drafting_rows

    async def issue_drafting_id(
        self, issue_drafting_id_request: ports.IssueDraftingIdRequest
    ) -> ports.IssueDraftingIdResponse:
        return ports.IssueDraftingIdResponse(drafting_id="issued-1")

    async def save_drafting(self, save_drafting_request: ports.SaveDraftingRequest) -> ports.SaveDraftingResponse:
        self._drafting_rows[save_drafting_request.drafting_row.drafting_id] = save_drafting_request.drafting_row
        return ports.SaveDraftingResponse(drafting_id=save_drafting_request.drafting_row.drafting_id)

    async def load_drafting(self, load_drafting_request: ports.LoadDraftingRequest) -> ports.LoadDraftingResponse:
        if load_drafting_request.drafting_id not in self._drafting_rows:
            return ports.LoadDraftingResponse(outcome=ports.LoadDraftingOutcome.NOT_FOUND, drafting_rows=())
        return ports.LoadDraftingResponse(
            outcome=ports.LoadDraftingOutcome.FOUND,
            drafting_rows=(self._drafting_rows[load_drafting_request.drafting_id],),
        )


@ts.fake
class FakeDraftingStore(ports.DraftingStore):

    def __init__(self) -> None:
        self.drafting_rows: dict[str, ports.DraftingRow] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.DraftingRepository]:
        yield FakeDraftingRepository(self.drafting_rows)


class TestDraftingService:

    async def test_drafting_stories_starts_the_drafting_of_the_job_under_the_issued_id(self) -> None:
        fake_drafting_orchestrator_relay = FakeDraftingOrchestratorRelay()
        drafting_service = application.DraftingService(FakeDraftingStore(), fake_drafting_orchestrator_relay)

        draft_stories_response = await drafting_service.draft_stories(client.DraftStoriesRequest(job="a job"))

        assert draft_stories_response.drafting_id == "issued-1"
        assert [
            (conduct_drafting_request.drafting_id, conduct_drafting_request.job)
            for conduct_drafting_request in fake_drafting_orchestrator_relay.started
        ] == [("issued-1", "a job")]

    async def test_a_started_drafting_is_saved_still_drafting_with_no_stories(self) -> None:
        fake_drafting_store = FakeDraftingStore()
        drafting_service = application.DraftingService(fake_drafting_store, FakeDraftingOrchestratorRelay())

        await drafting_service.draft_stories(client.DraftStoriesRequest(job="a job"))

        assert [
            (drafting_row.drafting_id, drafting_row.job, drafting_row.step, drafting_row.stories, drafting_row.accepted_stories)
            for drafting_row in fake_drafting_store.drafting_rows.values()
        ] == [("issued-1", "a job", "drafting", (), ())]

    async def test_a_blank_job_is_rejected_and_nothing_starts(self) -> None:
        fake_drafting_orchestrator_relay = FakeDraftingOrchestratorRelay()
        drafting_service = application.DraftingService(FakeDraftingStore(), fake_drafting_orchestrator_relay)

        with pytest.raises(client.DraftingRejected) as raised:
            await drafting_service.draft_stories(client.DraftStoriesRequest(job="  "))

        assert raised.value.code == "empty_job"
        assert fake_drafting_orchestrator_relay.started == []

    async def test_a_saved_drafting_is_read_back_by_its_id(self) -> None:
        fake_drafting_store = FakeDraftingStore()
        fake_drafting_store.drafting_rows["d1"] = ports.DraftingRow(
            drafting_id="d1",
            job="a job",
            step="awaiting_pick",
            stories=(ports.StoryRow(story_id="1", text="first"),),
            accepted_stories=(),
        )
        drafting_service = application.DraftingService(fake_drafting_store, FakeDraftingOrchestratorRelay())

        get_drafting_response = await drafting_service.get_drafting(client.GetDraftingRequest(drafting_id="d1"))

        assert (
            get_drafting_response.drafting.drafting_id,
            get_drafting_response.drafting.step,
            [(drafted_story.story_id, drafted_story.text) for drafted_story in get_drafting_response.drafting.stories],
            get_drafting_response.drafting.accepted_stories,
        ) == ("d1", "awaiting_pick", [("1", "first")], ())

    async def test_a_drafting_that_was_never_started_is_not_found(self) -> None:
        drafting_service = application.DraftingService(FakeDraftingStore(), FakeDraftingOrchestratorRelay())

        with pytest.raises(client.DraftingNotFound) as raised:
            await drafting_service.get_drafting(client.GetDraftingRequest(drafting_id="never-started"))

        assert str(raised.value) == "no drafting 'never-started'"

    async def test_an_empty_drafting_id_is_rejected(self) -> None:
        drafting_service = application.DraftingService(FakeDraftingStore(), FakeDraftingOrchestratorRelay())

        with pytest.raises(client.DraftingRejected) as raised:
            await drafting_service.get_drafting(client.GetDraftingRequest(drafting_id=""))

        assert raised.value.code == "empty_drafting_id"
