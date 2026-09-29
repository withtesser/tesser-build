from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays


class MapToRecordRunRequest(ts.Mapper, relays.RecordRunRequest):

    def __init__(self, draft_stories_request: relays.DraftStoriesRequest) -> None:
        super().__init__(
            run_id=draft_stories_request.run_id,
            job=draft_stories_request.job,
        )


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, record_run_response: relays.RecordRunResponse) -> None:
        super().__init__(run_id=record_run_response.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(self, run_actions_relay: relays.RunActionsRelay) -> None:
        self._run_actions_relay = run_actions_relay

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        record_run_response = await self._run_actions_relay.run_record_run(
            MapToRecordRunRequest(draft_stories_request)
        )
        return MapToDraftStoriesResponse(record_run_response)
