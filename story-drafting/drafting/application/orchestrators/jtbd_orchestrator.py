from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToRecordJtbdRequest(ts.Mapper, relays.RecordJtbdRequest):

    def __init__(self, draft_jtbd_request: relays.DraftJtbdRequest) -> None:
        super().__init__(
            jtbd_id=draft_jtbd_request.jtbd_id,
            situation=draft_jtbd_request.situation,
            motivation=draft_jtbd_request.motivation,
            outcome=draft_jtbd_request.outcome,
        )


class MapToDraftJtbdResponse(ts.Mapper, relays.DraftJtbdResponse):

    def __init__(self, record_jtbd_response: relays.RecordJtbdResponse) -> None:
        super().__init__(jtbd_id=record_jtbd_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def draft_jtbd(self, draft_jtbd_request: relays.DraftJtbdRequest) -> relays.DraftJtbdResponse:
        record_jtbd_response = await self._jtbd_actions_relay.run_record_jtbd(
            MapToRecordJtbdRequest(draft_jtbd_request)
        )
        return MapToDraftJtbdResponse(record_jtbd_response)
