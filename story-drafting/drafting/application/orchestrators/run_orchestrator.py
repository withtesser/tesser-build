from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays
import drafting.domain as domain


class MapToKeepRunRequest(ts.Mapper, relays.KeepRunRequest):

    def __init__(self, run_id: domain.RunId, job: domain.Job) -> None:
        super().__init__(run_id=str(run_id), job=str(job))


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, keep_run_response: relays.KeepRunResponse) -> None:
        super().__init__(run_id=keep_run_response.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(self, run_actions_relay: relays.RunActionsRelay) -> None:
        self._run_actions_relay = run_actions_relay

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        run_id = draft_stories_request.run_id
        job = draft_stories_request.job
        keep_run_response = await self._run_actions_relay.run_keep_run(MapToKeepRunRequest(run_id, job))
        return MapToDraftStoriesResponse(keep_run_response)
