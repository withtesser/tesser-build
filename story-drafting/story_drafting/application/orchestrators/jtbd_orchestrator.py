from __future__ import annotations

import tesser.application as ts

import story_drafting.application.relays as relays


class MapToBeginDraftingRequest(ts.Mapper, relays.BeginDraftingRequest):

    def __init__(self, begin_draft_process_request: relays.BeginDraftProcessRequest) -> None:
        super().__init__(
            jtbd_id=begin_draft_process_request.jtbd_id,
            status=begin_draft_process_request.status,
        )


class MapToBeginDraftProcessResponse(ts.Mapper, relays.BeginDraftProcessResponse):

    def __init__(self, begin_drafting_response: relays.BeginDraftingResponse) -> None:
        super().__init__(jtbd_id=begin_drafting_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def begin_draft_process(self, begin_draft_process_request: relays.BeginDraftProcessRequest) -> relays.BeginDraftProcessResponse:
        begin_drafting_response = await self._jtbd_actions_relay.run_begin_drafting(
            MapToBeginDraftingRequest(begin_draft_process_request)
        )
        return MapToBeginDraftProcessResponse(begin_drafting_response)
