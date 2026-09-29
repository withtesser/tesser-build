from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToRecordRunRequest(ts.Mapper, relays.RecordRunRequest):

    def __init__(self, conduct_run_request: relays.ConductRunRequest) -> None:
        super().__init__(
            run_id=conduct_run_request.run_id,
            job=conduct_run_request.job,
        )


class MapToConductRunResponse(ts.Mapper, relays.ConductRunResponse):

    def __init__(self, record_run_response: relays.RecordRunResponse) -> None:
        super().__init__(run_id=record_run_response.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(self, run_actions_relay: relays.RunActionsRelay) -> None:
        self._run_actions_relay = run_actions_relay

    async def conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.ConductRunResponse:
        record_run_response = await self._run_actions_relay.run_record_run(
            MapToRecordRunRequest(conduct_run_request)
        )
        return MapToConductRunResponse(record_run_response)
