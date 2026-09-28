from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays
import drafting.domain as domain


class MapToDraftStoriesRequest(ts.Mapper, relays.DraftStoriesRequest):

    def __init__(self, conduct_run_request: relays.ConductRunRequest) -> None:
        super().__init__(run_id=conduct_run_request.run_id, job=conduct_run_request.job)


class MapToRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(self, conduct_run_request: relays.ConductRunRequest) -> None:
        super().__init__(
            run_id=conduct_run_request.run_id,
            job=conduct_run_request.job,
            step=domain.DRAFTING,
            drafted_stories=(),
            accepted_stories=(),
        )


class MapToDraftedStoriesSpec(ts.Mapper, domain.DraftedStoriesSpec):

    def __init__(self, draft_stories_response: relays.DraftStoriesResponse) -> None:
        super().__init__(stories=draft_stories_response.stories)


class MapToRecordRunRequest(ts.Mapper, relays.RecordRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(
            run_id=str(run.identity),
            job=str(run.job),
            step=str(run.step),
            drafted_stories=tuple(str(story) for story in run.drafted_stories),
            accepted_stories=tuple(str(story) for story in run.accepted_stories),
        )


class MapToAwaitPickStoriesRequest(ts.Mapper, relays.AwaitPickStoriesRequest):

    def __init__(self, record_run_response: relays.RecordRunResponse) -> None:
        super().__init__(run_id=record_run_response.run_id)


class MapToConductRunResponse(ts.Mapper, relays.ConductRunResponse):

    def __init__(self, await_pick_stories_response: relays.AwaitPickStoriesResponse) -> None:
        super().__init__(run_id=await_pick_stories_response.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        drafting_actions_relay: relays.DraftingActionsRelay,
        run_actions_relay: relays.RunActionsRelay,
        run_orchestrator_signal_relay: relays.RunOrchestratorSignalRelay,
    ) -> None:
        self._drafting_actions_relay = drafting_actions_relay
        self._run_actions_relay = run_actions_relay
        self._run_orchestrator_signal_relay = run_orchestrator_signal_relay

    async def conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.ConductRunResponse:
        draft_stories_response = await self._drafting_actions_relay.run_draft_stories(
            MapToDraftStoriesRequest(conduct_run_request)
        )
        run = domain.Run(MapToRunSpec(conduct_run_request))
        run.stories_drafted(domain.DraftedStories(MapToDraftedStoriesSpec(draft_stories_response)))
        record_run_response = await self._run_actions_relay.run_record_run(MapToRecordRunRequest(run))
        await_pick_stories_response = await self._run_orchestrator_signal_relay.await_pick_stories(
            MapToAwaitPickStoriesRequest(record_run_response)
        )
        return MapToConductRunResponse(await_pick_stories_response)
