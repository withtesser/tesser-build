from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToDraftJtbdRequest(ts.Mapper, relays.DraftJtbdRequest):

    def __init__(self, arrange_drafting_request: relays.ArrangeDraftingRequest) -> None:
        super().__init__(
            jtbd_id=arrange_drafting_request.jtbd_id,
            status=arrange_drafting_request.status,
        )


class MapToArrangeDraftingResponse(ts.Mapper, relays.ArrangeDraftingResponse):

    def __init__(self, draft_jtbd_response: relays.DraftJtbdResponse) -> None:
        super().__init__(jtbd_id=draft_jtbd_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def arrange_drafting(self, arrange_drafting_request: relays.ArrangeDraftingRequest) -> relays.ArrangeDraftingResponse:
        draft_jtbd_response = await self._jtbd_actions_relay.run_draft_jtbd(
            MapToDraftJtbdRequest(arrange_drafting_request)
        )
        return MapToArrangeDraftingResponse(draft_jtbd_response)
