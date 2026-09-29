from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToWriteDraftsRequest(ts.Mapper, relays.WriteDraftsRequest):

    def __init__(self, draft_stories_request: relays.DraftStoriesRequest) -> None:
        super().__init__(
            jtbd_id=draft_stories_request.jtbd_id,
            job=draft_stories_request.job,
        )


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, write_drafts_response: relays.WriteDraftsResponse) -> None:
        super().__init__(jtbd_id=write_drafts_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        write_drafts_response = await self._jtbd_actions_relay.run_write_drafts(
            MapToWriteDraftsRequest(draft_stories_request)
        )
        return MapToDraftStoriesResponse(write_drafts_response)
