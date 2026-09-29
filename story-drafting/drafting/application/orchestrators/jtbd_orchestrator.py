from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToRecordJtbdRequest(ts.Mapper, relays.RecordJtbdRequest):

    def __init__(self, begin_drafting_request: relays.BeginDraftingRequest) -> None:
        super().__init__(
            jtbd_id=begin_drafting_request.jtbd_id,
            situation=begin_drafting_request.situation,
            motivation=begin_drafting_request.motivation,
            outcome=begin_drafting_request.outcome,
        )


class MapToBeginDraftingResponse(ts.Mapper, relays.BeginDraftingResponse):

    def __init__(self, record_jtbd_response: relays.RecordJtbdResponse) -> None:
        super().__init__(jtbd_id=record_jtbd_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def begin_drafting(self, begin_drafting_request: relays.BeginDraftingRequest) -> relays.BeginDraftingResponse:
        record_jtbd_response = await self._jtbd_actions_relay.run_record_jtbd(
            MapToRecordJtbdRequest(begin_drafting_request)
        )
        return MapToBeginDraftingResponse(record_jtbd_response)
