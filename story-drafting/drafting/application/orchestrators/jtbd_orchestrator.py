# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToDraftStoriesRequest(ts.Mapper, relays.DraftStoriesRequest):

    def __init__(self, draft_jtbd_stories_request: relays.DraftJtbdStoriesRequest) -> None:
        super().__init__(
            role=draft_jtbd_stories_request.role,
            i_want=draft_jtbd_stories_request.i_want,
            so_that=draft_jtbd_stories_request.so_that,
        )


class MapToRecordStoriesRequest(ts.Mapper, relays.RecordStoriesRequest):

    def __init__(self, draft_jtbd_stories_request: relays.DraftJtbdStoriesRequest, draft_stories_response: relays.DraftStoriesResponse) -> None:
        super().__init__(
            jtbd_id=draft_jtbd_stories_request.jtbd_id,
            role=draft_jtbd_stories_request.role,
            i_want=draft_jtbd_stories_request.i_want,
            so_that=draft_jtbd_stories_request.so_that,
            story_texts=tuple(relays.JtbdActionsStoryText(given=story_text.given, when=story_text.when, then=story_text.then) for story_text in draft_stories_response.story_texts),
        )


class MapToDraftJtbdStoriesResponse(ts.Mapper, relays.DraftJtbdStoriesResponse):

    def __init__(self, record_stories_response: relays.RecordStoriesResponse) -> None:
        super().__init__(
            jtbd_id=record_stories_response.jtbd_id,
        )


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        story_actions_relay: relays.StoryActionsRelay,
        jtbd_actions_relay: relays.JtbdActionsRelay,
    ) -> None:
        self._story_actions_relay = story_actions_relay
        self._jtbd_actions_relay = jtbd_actions_relay

    async def draft_jtbd_stories(self, draft_jtbd_stories_request: relays.DraftJtbdStoriesRequest) -> relays.DraftJtbdStoriesResponse:
        draft_stories_response = await self._story_actions_relay.run_draft_stories(MapToDraftStoriesRequest(draft_jtbd_stories_request))
        record_stories_response = await self._jtbd_actions_relay.run_record_stories(MapToRecordStoriesRequest(draft_jtbd_stories_request, draft_stories_response))
        return MapToDraftJtbdStoriesResponse(record_stories_response)
