# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToDraftStoriesRequest(ts.Mapper, relays.DraftStoriesRequest):

    def __init__(self, story_drafting_request: relays.StoryDraftingRequest) -> None:
        super().__init__(
            jtbd_id=story_drafting_request.jtbd_id,
            role=story_drafting_request.role,
            i_want=story_drafting_request.i_want,
            so_that=story_drafting_request.so_that,
        )


class MapToStoryDraftingResponse(ts.Mapper, relays.StoryDraftingResponse):

    def __init__(self, draft_stories_response: relays.DraftStoriesResponse) -> None:
        super().__init__(
            jtbd_id=draft_stories_response.jtbd_id,
        )


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        jtbd_actions_relay: relays.JtbdActionsRelay,
    ) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def story_drafting(self, story_drafting_request: relays.StoryDraftingRequest) -> relays.StoryDraftingResponse:
        draft_stories_response = await self._jtbd_actions_relay.run_draft_stories(MapToDraftStoriesRequest(story_drafting_request))
        return MapToStoryDraftingResponse(draft_stories_response)
