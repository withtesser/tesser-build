from __future__ import annotations

import tesser.application as ts

import jtbds.application.relays as relays


class MapToInitializeJtbdRequest(ts.Mapper, relays.InitializeJtbdRequest):

    def __init__(self, process_jtbd_request: relays.ProcessJtbdRequest) -> None:
        super().__init__(
            jtbd_id=process_jtbd_request.jtbd_id,
            description=process_jtbd_request.description,
            status=process_jtbd_request.status,
        )


class MapToProcessJtbdResponse(ts.Mapper, relays.ProcessJtbdResponse):

    def __init__(self, initialize_jtbd_response: relays.InitializeJtbdResponse) -> None:
        super().__init__(jtbd_id=initialize_jtbd_response.jtbd_id)


class JobToBeDoneOrchestrator(ts.Orchestrator):

    def __init__(self, job_to_be_done_actions_relay: relays.JobToBeDoneActionsRelay) -> None:
        self._job_to_be_done_actions_relay = job_to_be_done_actions_relay

    async def process_jtbd(self, process_jtbd_request: relays.ProcessJtbdRequest) -> relays.ProcessJtbdResponse:
        initialize_jtbd_response = await self._job_to_be_done_actions_relay.run_initialize_jtbd(
            MapToInitializeJtbdRequest(process_jtbd_request)
        )
        return MapToProcessJtbdResponse(initialize_jtbd_response)
