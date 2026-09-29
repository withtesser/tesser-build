from __future__ import annotations

import tesser.application as ts

import story_drafting.application.relays as relays


class MapToInitializeJtbdRequest(ts.Mapper, relays.InitializeJtbdRequest):

    def __init__(self, conduct_drafting_request: relays.ConductDraftingRequest) -> None:
        super().__init__(
            jtbd_id=conduct_drafting_request.jtbd_id,
            status=conduct_drafting_request.status,
        )


class MapToConductDraftingResponse(ts.Mapper, relays.ConductDraftingResponse):

    def __init__(self, initialize_jtbd_response: relays.InitializeJtbdResponse) -> None:
        super().__init__(jtbd_id=initialize_jtbd_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def conduct_drafting(self, conduct_drafting_request: relays.ConductDraftingRequest) -> relays.ConductDraftingResponse:
        initialize_jtbd_response = await self._jtbd_actions_relay.run_initialize_jtbd(
            MapToInitializeJtbdRequest(conduct_drafting_request)
        )
        return MapToConductDraftingResponse(initialize_jtbd_response)
