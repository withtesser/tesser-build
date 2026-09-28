from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToConductRunResponse(ts.Mapper, relays.ConductRunResponse):

    def __init__(self, conduct_run_request: relays.ConductRunRequest) -> None:
        super().__init__(run_id=conduct_run_request.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(self) -> None:
        return None

    async def conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.ConductRunResponse:
        return MapToConductRunResponse(conduct_run_request)
