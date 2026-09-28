from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client
import drafting.domain as domain
import tesser.errors as errors


class MapToRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(self, issue_run_id_response: ports.IssueRunIdResponse, open_run_request: client.OpenRunRequest) -> None:
        super().__init__(
            run_id=issue_run_id_response.run_id,
            job=open_run_request.job,
            step=domain.DRAFTING,
            drafted_stories=(),
            accepted_stories=(),
        )


class MapToSaveRunRequest(ts.Mapper, ports.SaveRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(
            run_id=str(run.identity),
            job=str(run.job),
            step=str(run.step),
            drafted_stories=tuple(str(story) for story in run.drafted_stories),
            accepted_stories=tuple(str(story) for story in run.accepted_stories),
        )


class MapToConductRunRequest(ts.Mapper, relays.ConductRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(run_id=str(run.identity), job=str(run.job))


class MapToOpenRunResponse(ts.Mapper, client.OpenRunResponse):

    def __init__(self, start_conduct_run_response: relays.StartConductRunResponse) -> None:
        super().__init__(run_id=start_conduct_run_response.run_id)


class MapToLoadRunRequest(ts.Mapper, ports.LoadRunRequest):

    def __init__(self, run_id: domain.RunId) -> None:
        super().__init__(run_id=str(run_id))


class MapToRunPresenceSpec(ts.Mapper, domain.RunPresenceSpec):

    def __init__(self, load_run_response: ports.LoadRunResponse) -> None:
        super().__init__(presence=load_run_response.outcome.value)


class MapToRun(ts.Mapper, client.Run):

    def __init__(self, run: ports.Run) -> None:
        super().__init__(
            run_id=run.run_id,
            job=run.job,
            step=run.step,
            drafted_stories=run.drafted_stories,
            accepted_stories=run.accepted_stories,
        )


class MapToGetRunResponse(ts.Mapper, client.GetRunResponse):

    def __init__(self, run: ports.Run) -> None:
        super().__init__(run=MapToRun(run))


class RunService(ts.ApplicationService):

    def __init__(self, run_store: ports.RunStore, run_orchestrator_relay: relays.RunOrchestratorRelay) -> None:
        self._run_store = run_store
        self._run_orchestrator_relay = run_orchestrator_relay

    async def open_run(self, open_run_request: client.OpenRunRequest) -> client.OpenRunResponse:
        async with self._run_store.transaction() as run_repository:
            issue_run_id_response = await run_repository.issue_run_id(ports.IssueRunIdRequest())
        try:
            run = domain.Run(MapToRunSpec(issue_run_id_response, open_run_request))
        except errors.DomainError as domain_error:
            raise client.RunRejected(domain_error.code, domain_error.message) from domain_error
        async with self._run_store.transaction() as run_repository:
            await run_repository.save_run(MapToSaveRunRequest(run))
        start_conduct_run_response = await self._run_orchestrator_relay.start_conduct_run(MapToConductRunRequest(run))
        return MapToOpenRunResponse(start_conduct_run_response)

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        try:
            run_id = domain.RunId(get_run_request.run_id)
        except errors.DomainError as domain_error:
            raise client.RunRejected(domain_error.code, domain_error.message) from domain_error
        async with self._run_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(MapToLoadRunRequest(run_id))
        match domain.RunPresence(MapToRunPresenceSpec(load_run_response)).decide():
            case domain.RunLookup.FOUND:
                return MapToGetRunResponse(load_run_response.runs[0])
            case domain.RunLookup.NOT_FOUND:
                raise client.RunNotFound(f"no run {get_run_request.run_id!r}")
            case _ as never:
                typing.assert_never(never)
