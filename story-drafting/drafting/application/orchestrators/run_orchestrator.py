from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays
import drafting.domain as domain


class MapToRecordRunRequest(ts.Mapper, relays.RecordRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(run=run)


class MapToWriteStoriesRequest(ts.Mapper, relays.WriteStoriesRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(job=str(run.job))


class MapToDraftSpec(ts.Mapper, domain.DraftSpec):

    def __init__(self, write_stories_response: relays.WriteStoriesResponse) -> None:
        super().__init__(stories=tuple(domain.StorySpec(text=story) for story in write_stories_response.stories))


class MapToAwaitPickStoryRequest(ts.Mapper, relays.AwaitPickStoryRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(run_id=str(run.identity))


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, record_run_response: relays.RecordRunResponse) -> None:
        super().__init__(run_id=record_run_response.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        run_actions_relay: relays.RunActionsRelay,
        story_actions_relay: relays.StoryActionsRelay,
        run_orchestrator_signal_relay: relays.RunOrchestratorSignalRelay,
    ) -> None:
        self._run_actions_relay = run_actions_relay
        self._story_actions_relay = story_actions_relay
        self._run_orchestrator_signal_relay = run_orchestrator_signal_relay

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        run = draft_stories_request.run
        await self._run_actions_relay.run_record_run(MapToRecordRunRequest(run))
        write_stories_response = await self._story_actions_relay.run_write_stories(MapToWriteStoriesRequest(run))
        run.drafted(domain.Draft(MapToDraftSpec(write_stories_response)))
        record_run_response = await self._run_actions_relay.run_record_run(MapToRecordRunRequest(run))
        await self._run_orchestrator_signal_relay.await_pick_story(MapToAwaitPickStoryRequest(run))
        return MapToDraftStoriesResponse(record_run_response)
