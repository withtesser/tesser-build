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


class MapToRecordDraftedStoriesRequest(ts.Mapper, relays.RecordDraftedStoriesRequest):

    def __init__(self, story_drafting_request: relays.StoryDraftingRequest, draft_stories_response: relays.DraftStoriesResponse) -> None:
        super().__init__(
            jtbd_id=story_drafting_request.jtbd_id,
            role=story_drafting_request.role,
            i_want=story_drafting_request.i_want,
            so_that=story_drafting_request.so_that,
            story_texts=tuple(relays.JtbdActionsStoryText(given=story_text.given, when=story_text.when, then=story_text.then) for story_text in draft_stories_response.story_texts),
        )


class MapToStoryDraftingResponse(ts.Mapper, relays.StoryDraftingResponse):

    def __init__(self, record_drafted_stories_response: relays.RecordDraftedStoriesResponse) -> None:
        super().__init__(
            jtbd_id=record_drafted_stories_response.jtbd_id,
        )


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        story_actions_relay: relays.StoryActionsRelay,
        jtbd_actions_relay: relays.JtbdActionsRelay,
    ) -> None:
        self._story_actions_relay = story_actions_relay
        self._jtbd_actions_relay = jtbd_actions_relay

    async def story_drafting(self, story_drafting_request: relays.StoryDraftingRequest) -> relays.StoryDraftingResponse:
        draft_stories_response = await self._story_actions_relay.run_draft_stories(MapToDraftStoriesRequest(story_drafting_request))
        record_drafted_stories_response = await self._jtbd_actions_relay.run_record_drafted_stories(MapToRecordDraftedStoriesRequest(story_drafting_request, draft_stories_response))
        return MapToStoryDraftingResponse(record_drafted_stories_response)
