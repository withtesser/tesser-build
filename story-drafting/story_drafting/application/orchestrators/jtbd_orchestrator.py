from __future__ import annotations

import tesser.application as ts

import story_drafting.application.relays as relays


class MapToWriteDraftsRequest(ts.Mapper, relays.WriteDraftsRequest):

    def __init__(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> None:
        super().__init__(
            jtbd_id=work_through_jtbd_request.jtbd_id,
            job=work_through_jtbd_request.job,
        )


class MapToWorkThroughJtbdResponse(ts.Mapper, relays.WorkThroughJtbdResponse):

    def __init__(self, write_drafts_response: relays.WriteDraftsResponse) -> None:
        super().__init__(jtbd_id=write_drafts_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def work_through_jtbd(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> relays.WorkThroughJtbdResponse:
        write_drafts_response = await self._jtbd_actions_relay.run_write_drafts(
            MapToWriteDraftsRequest(work_through_jtbd_request)
        )
        return MapToWorkThroughJtbdResponse(write_drafts_response)
