from __future__ import annotations

import typing

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client
import drafting.domain as domain
import tesser.errors as errors

_DRAFTING: typing.Final[str] = "drafting"


class MapToRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(self, open_run_request: client.OpenRunRequest) -> None:
        super().__init__(
            run_id=open_run_request.run_id,
            job=open_run_request.job,
            stage=_DRAFTING,
            stories=(),
            accepted_stories=(),
        )


class MapToDraftStoriesRequest(ts.Mapper, relays.DraftStoriesRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(run=run)


class MapToOpenRunResponse(ts.Mapper, client.OpenRunResponse):

    def __init__(self, start_draft_stories_response: relays.StartDraftStoriesResponse) -> None:
        super().__init__(run_id=start_draft_stories_response.run_id)


class MapToLoadRunRequest(ts.Mapper, ports.LoadRunRequest):

    def __init__(self, run_id: domain.RunId) -> None:
        super().__init__(run_id=str(run_id))


class MapToLoadedRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(self, load_run_request: ports.LoadRunRequest, load_run_response: ports.LoadRunResponse) -> None:
        match load_run_response.outcome:
            case ports.LoadRunOutcome.FOUND:
                run_record = load_run_response.runs[0]
            case ports.LoadRunOutcome.NOT_FOUND:
                raise client.RunNotFound(f"no run {load_run_request.run_id!r}")
            case _ as never:
                typing.assert_never(never)
        super().__init__(
            run_id=run_record.run_id,
            job=run_record.job,
            stage=run_record.stage,
            stories=tuple(domain.StorySpec(text=story) for story in run_record.stories),
            accepted_stories=tuple(domain.StorySpec(text=story) for story in run_record.accepted_stories),
        )


class MapToGetRunResponse(ts.Mapper, client.GetRunResponse):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(
            run_id=str(run.identity),
            job=str(run.job),
            stage=str(run.stage),
            stories=tuple(str(story) for story in run.stories),
            accepted_stories=tuple(str(story) for story in run.accepted_stories),
        )


class DraftingService(ts.ApplicationService):

    def __init__(self, run_store: ports.RunStore, run_orchestrator_relay: relays.RunOrchestratorRelay) -> None:
        self._run_store = run_store
        self._run_orchestrator_relay = run_orchestrator_relay

    async def open_run(self, open_run_request: client.OpenRunRequest) -> client.OpenRunResponse:
        try:
            run = domain.Run(MapToRunSpec(open_run_request))
        except errors.DomainError as domain_error:
            raise client.RunRejected(domain_error.code, domain_error.message) from domain_error
        start_draft_stories_response = await self._run_orchestrator_relay.start_draft_stories(MapToDraftStoriesRequest(run))
        return MapToOpenRunResponse(start_draft_stories_response)

    async def get_run(self, get_run_request: client.GetRunRequest) -> client.GetRunResponse:
        try:
            run_id = domain.RunId(get_run_request.run_id)
        except errors.DomainError as domain_error:
            raise client.RunRejected(domain_error.code, domain_error.message) from domain_error
        load_run_request = MapToLoadRunRequest(run_id)
        async with self._run_store.transaction() as run_repository:
            load_run_response = await run_repository.load_run(load_run_request)
        run = domain.Run(MapToLoadedRunSpec(load_run_request, load_run_response))
        return MapToGetRunResponse(run)
