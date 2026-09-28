from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client
import drafting.domain as domain
import tesser.errors as errors

_NOT_FOUND: typing.Final[str] = "no run has that id"


class MapToDraftStoriesRequest(ts.Mapper, relays.DraftStoriesRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(run_id=run.identity, job=run.job)


class MapToRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(self, begin_run_request: client.BeginRunRequest) -> None:
        super().__init__(run_id=begin_run_request.run_id, job=begin_run_request.job)


class MapToBeginRunResponse(ts.Mapper, client.BeginRunResponse):

    def __init__(self, start_draft_stories_response: relays.StartDraftStoriesResponse) -> None:
        super().__init__(run_id=start_draft_stories_response.run_id)


class MapToGetRunRequest(ts.Mapper, ports.GetRunRequest):

    def __init__(self, run_id: domain.RunId) -> None:
        super().__init__(run_id=str(run_id))


class MapToGetRunResponse(ts.Mapper, client.GetRunResponse):

    def __init__(self, get_run_response: ports.GetRunResponse) -> None:
        super().__init__(
            run_id=get_run_response.runs[0].run_id,
            job=get_run_response.runs[0].job,
            stage=get_run_response.runs[0].stage,
            stories=tuple(client.Story(text=story.text) for story in get_run_response.runs[0].stories),
            accepted_stories=tuple(
                client.Story(text=story.text) for story in get_run_response.runs[0].accepted_stories
            ),
        )


class RunService(ts.ApplicationService):

    def __init__(self, run_repository: ports.RunRepository, run_orchestrator_relay: relays.RunOrchestratorRelay) -> None:
        self._run_repository = run_repository
        self._run_orchestrator_relay = run_orchestrator_relay

    async def begin_run(self, begin_run_request: client.BeginRunRequest) -> client.BeginRunResponse:
        try:
            run = domain.Run(MapToRunSpec(begin_run_request))
        except errors.DomainError as domain_error:
            raise client.RunRejected(domain_error.code, domain_error.message) from domain_error
        start_draft_stories_response = await self._run_orchestrator_relay.start_draft_stories(
            MapToDraftStoriesRequest(run)
        )
        return MapToBeginRunResponse(start_draft_stories_response)

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        try:
            run_id = domain.RunId(get_run_request.run_id)
        except errors.DomainError as domain_error:
            raise client.RunRejected(domain_error.code, domain_error.message) from domain_error
        get_run_response = await self._run_repository.get_run(MapToGetRunRequest(run_id))
        match get_run_response.outcome:  # tesser:debt TB082
            case ports.GetRunOutcome.FOUND:
                return MapToGetRunResponse(get_run_response)
            case ports.GetRunOutcome.NOT_FOUND:
                raise client.RunNotFound(_NOT_FOUND)
            case _ as never:
                typing.assert_never(never)
