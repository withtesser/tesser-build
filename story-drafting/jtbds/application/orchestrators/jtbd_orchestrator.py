from __future__ import annotations

import tesser.application as ts

import jtbds.application.relays as relays


class MapToDraftJtbdRequest(ts.Mapper, relays.DraftJtbdRequest):

    def __init__(self, process_jtbd_request: relays.ProcessJtbdRequest) -> None:
        super().__init__(
            jtbd_id=process_jtbd_request.jtbd_id,
            description=process_jtbd_request.description,
            status=process_jtbd_request.status,
        )


class MapToProcessJtbdResponse(ts.Mapper, relays.ProcessJtbdResponse):

    def __init__(self, draft_jtbd_response: relays.DraftJtbdResponse) -> None:
        super().__init__(jtbd_id=draft_jtbd_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def process_jtbd(self, process_jtbd_request: relays.ProcessJtbdRequest) -> relays.ProcessJtbdResponse:
        draft_jtbd_response = await self._jtbd_actions_relay.run_draft_jtbd(
            MapToDraftJtbdRequest(process_jtbd_request)
        )
        return MapToProcessJtbdResponse(draft_jtbd_response)
