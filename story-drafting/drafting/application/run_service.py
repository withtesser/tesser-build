from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client
import drafting.domain as domain


class MapToRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(
        self,
        begin_run_request: client.BeginRunRequest,
        issue_run_id_response: ports.IssueRunIdResponse,
    ) -> None:
        super().__init__(
            run_id=issue_run_id_response.run_id,
            job=begin_run_request.job,
        )


class MapToConductRunRequest(ts.Mapper, relays.ConductRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(
            run_id=str(run.identity),
            job=str(run.job),
        )


class MapToBeginRunResponse(ts.Mapper, client.BeginRunResponse):

    def __init__(self, conduct_run_response: relays.ConductRunResponse) -> None:
        super().__init__(run_id=conduct_run_response.run_id)


class MapToLoadRunRequest(ts.Mapper, ports.LoadRunRequest):

    def __init__(self, run_id: domain.RunId) -> None:
        super().__init__(run_id=str(run_id))


class MapToRun(ts.Mapper, client.Run):

    def __init__(self, run: ports.Run) -> None:
        super().__init__(run_id=run.run_id, job=run.job)


class MapToGetRunResponse(ts.Mapper, client.GetRunResponse):

    def __init__(self, load_run_response: ports.LoadRunResponse) -> None:
        super().__init__(run=MapToRun(load_run_response.runs[0]))


class RunService(ts.ApplicationService):

    def __init__(
        self,
        run_orchestrator_relay: relays.RunOrchestratorRelay,
        run_identity_repository: ports.RunIdentityRepository,
        run_store: ports.RunStore,
    ) -> None:
        self._run_orchestrator_relay = run_orchestrator_relay
        self._run_identity_repository = run_identity_repository
        self._run_store = run_store

    async def begin_run(self, begin_run_request: client.BeginRunRequest) -> client.BeginRunResponse:
        issue_run_id_response = await self._run_identity_repository.issue_run_id(ports.IssueRunIdRequest())
        run = domain.Run(MapToRunSpec(begin_run_request, issue_run_id_response))
        conduct_run_response = await self._run_orchestrator_relay.run_conduct_run(MapToConductRunRequest(run))
        return MapToBeginRunResponse(conduct_run_response)

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        run_id = domain.RunId(get_run_request.run_id)
        async with self._run_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(MapToLoadRunRequest(run_id))
        return MapToGetRunResponse(load_run_response)
