from __future__ import annotations

import tesser.application as ts

import jtbd.application.relays as relays


class MapToMarkJtbdDraftingRequest(ts.Mapper, relays.MarkJtbdDraftingRequest):

    def __init__(self, draft_for_jtbd_request: relays.DraftForJtbdRequest) -> None:
        super().__init__(
            jtbd_id=draft_for_jtbd_request.jtbd_id,
            description=draft_for_jtbd_request.description,
            status=draft_for_jtbd_request.status,
        )


class MapToDraftForJtbdResponse(ts.Mapper, relays.DraftForJtbdResponse):

    def __init__(self, mark_jtbd_drafting_response: relays.MarkJtbdDraftingResponse) -> None:
        super().__init__(jtbd_id=mark_jtbd_drafting_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def draft_for_jtbd(self, draft_for_jtbd_request: relays.DraftForJtbdRequest) -> relays.DraftForJtbdResponse:
        mark_jtbd_drafting_response = await self._jtbd_actions_relay.run_mark_jtbd_drafting(
            MapToMarkJtbdDraftingRequest(draft_for_jtbd_request)
        )
        return MapToDraftForJtbdResponse(mark_jtbd_drafting_response)
