from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client
import drafting.domain as domain
import tesser.errors as errors


class MapToDraftingSpec(ts.Mapper, domain.DraftingSpec):

    def __init__(self, issue_drafting_id_response: ports.IssueDraftingIdResponse, job: domain.Job) -> None:
        super().__init__(
            drafting_id=issue_drafting_id_response.drafting_id,
            job=str(job),
            step="drafting",
            stories=(),
            accepted_stories=(),
        )


class MapToStoryRow(ts.Mapper, ports.StoryRow):

    def __init__(self, story: domain.Story) -> None:
        super().__init__(story_id=str(story.identity), text=str(story.text))


class MapToDraftingRow(ts.Mapper, ports.DraftingRow):

    def __init__(self, drafting: domain.Drafting) -> None:
        super().__init__(
            drafting_id=str(drafting.identity),
            job=str(drafting.job),
            step=str(drafting.step),
            stories=tuple(MapToStoryRow(story) for story in drafting.stories),
            accepted_stories=tuple(MapToStoryRow(story) for story in drafting.accepted_stories),
        )


class MapToSaveDraftingRequest(ts.Mapper, ports.SaveDraftingRequest):

    def __init__(self, drafting: domain.Drafting) -> None:
        super().__init__(drafting_row=MapToDraftingRow(drafting))


class MapToConductDraftingRequest(ts.Mapper, relays.ConductDraftingRequest):

    def __init__(self, drafting: domain.Drafting) -> None:
        super().__init__(drafting_id=str(drafting.identity), job=str(drafting.job))


class MapToDraftStoriesResponse(ts.Mapper, client.DraftStoriesResponse):

    def __init__(self, start_conduct_drafting_response: relays.StartConductDraftingResponse) -> None:
        super().__init__(drafting_id=start_conduct_drafting_response.drafting_id)


class MapToLoadDraftingRequest(ts.Mapper, ports.LoadDraftingRequest):

    def __init__(self, drafting_id: domain.DraftingId) -> None:
        super().__init__(drafting_id=str(drafting_id))


class MapToDraftingPresenceSpec(ts.Mapper, domain.DraftingPresenceSpec):

    def __init__(self, load_drafting_response: ports.LoadDraftingResponse) -> None:
        super().__init__(presence=load_drafting_response.outcome.value)


class MapToDraftedStory(ts.Mapper, client.DraftedStory):

    def __init__(self, story_row: ports.StoryRow) -> None:
        super().__init__(story_id=story_row.story_id, text=story_row.text)


class MapToDrafting(ts.Mapper, client.Drafting):

    def __init__(self, drafting_row: ports.DraftingRow) -> None:
        super().__init__(
            drafting_id=drafting_row.drafting_id,
            step=drafting_row.step,
            stories=tuple(MapToDraftedStory(story_row) for story_row in drafting_row.stories),
            accepted_stories=tuple(MapToDraftedStory(story_row) for story_row in drafting_row.accepted_stories),
        )


class MapToGetDraftingResponse(ts.Mapper, client.GetDraftingResponse):

    def __init__(self, drafting_row: ports.DraftingRow) -> None:
        super().__init__(drafting=MapToDrafting(drafting_row))


class DraftingService(ts.ApplicationService):

    def __init__(
        self, drafting_store: ports.DraftingStore, drafting_orchestrator_relay: relays.DraftingOrchestratorRelay
    ) -> None:
        self._drafting_store = drafting_store
        self._drafting_orchestrator_relay = drafting_orchestrator_relay

    async def draft_stories(
        self, draft_stories_request: client.DraftStoriesRequest
    ) -> client.DraftStoriesResponse:
        try:
            job = domain.Job(draft_stories_request.job)
        except errors.DomainError as domain_error:
            raise client.DraftingRejected(domain_error.code, domain_error.message) from domain_error
        async with self._drafting_store.transaction() as drafting_repository:
            issue_drafting_id_response = await drafting_repository.issue_drafting_id(ports.IssueDraftingIdRequest())
            drafting = domain.Drafting(MapToDraftingSpec(issue_drafting_id_response, job))
            await drafting_repository.save_drafting(MapToSaveDraftingRequest(drafting))
        start_conduct_drafting_response = await self._drafting_orchestrator_relay.start_conduct_drafting(
            MapToConductDraftingRequest(drafting)
        )
        return MapToDraftStoriesResponse(start_conduct_drafting_response)

    async def get_drafting(self, get_drafting_request: client.GetDraftingRequest) -> client.GetDraftingResponse:
        try:
            drafting_id = domain.DraftingId(get_drafting_request.drafting_id)
        except errors.DomainError as domain_error:
            raise client.DraftingRejected(domain_error.code, domain_error.message) from domain_error
        async with self._drafting_store.transaction() as drafting_repository:
            load_drafting_response = await drafting_repository.load_drafting(MapToLoadDraftingRequest(drafting_id))
        match domain.DraftingPresence(MapToDraftingPresenceSpec(load_drafting_response)).decide():
            case domain.DraftingLookup.FOUND:
                return MapToGetDraftingResponse(load_drafting_response.drafting_rows[0])
            case domain.DraftingLookup.NOT_FOUND:
                raise client.DraftingNotFound(f"no drafting {get_drafting_request.drafting_id!r}")
            case _ as never:
                typing.assert_never(never)
