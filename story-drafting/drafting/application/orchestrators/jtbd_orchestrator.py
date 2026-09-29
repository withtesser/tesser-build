from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToRecordJtbdRequest(ts.Mapper, relays.RecordJtbdRequest):

    def __init__(self, draft_stories_request: relays.DraftStoriesRequest) -> None:
        super().__init__(
            jtbd_id=draft_stories_request.jtbd_id,
            situation=draft_stories_request.situation,
            motivation=draft_stories_request.motivation,
            outcome=draft_stories_request.outcome,
        )


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, record_jtbd_response: relays.RecordJtbdResponse) -> None:
        super().__init__(jtbd_id=record_jtbd_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        record_jtbd_response = await self._jtbd_actions_relay.run_record_jtbd(
            MapToRecordJtbdRequest(draft_stories_request)
        )
        return MapToDraftStoriesResponse(record_jtbd_response)
