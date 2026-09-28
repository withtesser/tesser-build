from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToWriteStoriesRequest(ts.Mapper, relays.WriteStoriesRequest):

    def __init__(self, conduct_drafting_request: relays.ConductDraftingRequest) -> None:
        super().__init__(job=conduct_drafting_request.job)


class MapToKeepDraftedStoriesRequest(ts.Mapper, relays.KeepDraftedStoriesRequest):

    def __init__(
        self, conduct_drafting_request: relays.ConductDraftingRequest, write_stories_response: relays.WriteStoriesResponse
    ) -> None:
        super().__init__(
            drafting_id=conduct_drafting_request.drafting_id,
            job=conduct_drafting_request.job,
            texts=write_stories_response.texts,
        )


class MapToAwaitPickStoryRequest(ts.Mapper, relays.AwaitPickStoryRequest):

    def __init__(self, keep_drafted_stories_response: relays.KeepDraftedStoriesResponse) -> None:
        super().__init__(drafting_id=keep_drafted_stories_response.drafting_id)


class MapToConductDraftingResponse(ts.Mapper, relays.ConductDraftingResponse):

    def __init__(self, keep_drafted_stories_response: relays.KeepDraftedStoriesResponse) -> None:
        super().__init__(drafting_id=keep_drafted_stories_response.drafting_id)


class DraftingOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        writing_actions_relay: relays.WritingActionsRelay,
        drafting_actions_relay: relays.DraftingActionsRelay,
        drafting_orchestrator_signal_relay: relays.DraftingOrchestratorSignalRelay,
    ) -> None:
        self._writing_actions_relay = writing_actions_relay
        self._drafting_actions_relay = drafting_actions_relay
        self._drafting_orchestrator_signal_relay = drafting_orchestrator_signal_relay

    async def conduct_drafting(
        self, conduct_drafting_request: relays.ConductDraftingRequest
    ) -> relays.ConductDraftingResponse:
        write_stories_response = await self._writing_actions_relay.run_write_stories(
            MapToWriteStoriesRequest(conduct_drafting_request)
        )
        keep_drafted_stories_response = await self._drafting_actions_relay.run_keep_drafted_stories(
            MapToKeepDraftedStoriesRequest(conduct_drafting_request, write_stories_response)
        )
        await self._drafting_orchestrator_signal_relay.await_pick_story(
            MapToAwaitPickStoryRequest(keep_drafted_stories_response)
        )
        return MapToConductDraftingResponse(keep_drafted_stories_response)
