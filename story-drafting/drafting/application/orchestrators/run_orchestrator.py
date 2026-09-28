from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays
import drafting.domain as domain


class MapToRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(self, draft_stories_request: relays.DraftStoriesRequest) -> None:
        super().__init__(run_id=draft_stories_request.run_id, job=draft_stories_request.job)


class MapToRecordRunRequest(ts.Mapper, relays.RecordRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(
            run_id=str(run.identity),
            job=str(run.job),
            stage=str(run.stage),
            stories=tuple(str(story) for story in run.stories),
            accepted_stories=tuple(str(story) for story in run.accepted_stories),
        )


class MapToWriteStoriesRequest(ts.Mapper, relays.WriteStoriesRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(job=str(run.job))


class MapToDraftSpec(ts.Mapper, domain.DraftSpec):

    def __init__(self, write_stories_response: relays.WriteStoriesResponse) -> None:
        super().__init__(stories=write_stories_response.stories)


class MapToAwaitPickStoriesRequest(ts.Mapper, relays.AwaitPickStoriesRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(run_id=str(run.identity))


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, record_run_response: relays.RecordRunResponse) -> None:
        super().__init__(run_id=record_run_response.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        run_actions_relay: relays.RunActionsRelay,
        story_writing_actions_relay: relays.StoryWritingActionsRelay,
        run_orchestrator_signal_relay: relays.RunOrchestratorSignalRelay,
    ) -> None:
        self._run_actions_relay = run_actions_relay
        self._story_writing_actions_relay = story_writing_actions_relay
        self._run_orchestrator_signal_relay = run_orchestrator_signal_relay

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        run = domain.Run(MapToRunSpec(draft_stories_request))
        await self._run_actions_relay.run_record_run(MapToRecordRunRequest(run))
        write_stories_response = await self._story_writing_actions_relay.run_write_stories(
            MapToWriteStoriesRequest(run)
        )
        run.draft(domain.Draft(MapToDraftSpec(write_stories_response)))
        record_run_response = await self._run_actions_relay.run_record_run(MapToRecordRunRequest(run))
        await self._run_orchestrator_signal_relay.await_pick_stories(MapToAwaitPickStoriesRequest(run))
        return MapToDraftStoriesResponse(record_run_response)
