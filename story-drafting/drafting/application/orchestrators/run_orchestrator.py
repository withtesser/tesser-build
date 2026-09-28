from __future__ import annotations

import tesser.application as ts

import drafting.application.relays as relays
import drafting.domain as domain


class MapToKeepRunRequest(ts.Mapper, relays.KeepRunRequest):

    def __init__(self, run_id: domain.RunId, job: domain.Job) -> None:
        super().__init__(run_id=str(run_id), job=str(job))


class MapToWriteStoriesRequest(ts.Mapper, relays.WriteStoriesRequest):

    def __init__(self, job: domain.Job) -> None:
        super().__init__(job=str(job))


class MapToOfferStoriesRequest(ts.Mapper, relays.OfferStoriesRequest):

    def __init__(
        self, run_id: domain.RunId, job: domain.Job, write_stories_response: relays.WriteStoriesResponse
    ) -> None:
        super().__init__(run_id=str(run_id), job=str(job), stories=write_stories_response.stories)


class MapToAwaitPickStoriesRequest(ts.Mapper, relays.AwaitPickStoriesRequest):

    def __init__(self, offer_stories_response: relays.OfferStoriesResponse) -> None:
        super().__init__(run_id=offer_stories_response.run_id)


class MapToDraftStoriesResponse(ts.Mapper, relays.DraftStoriesResponse):

    def __init__(self, await_pick_stories_response: relays.AwaitPickStoriesResponse) -> None:
        super().__init__(run_id=await_pick_stories_response.run_id)


class RunOrchestrator(ts.Orchestrator):

    def __init__(
        self,
        run_actions_relay: relays.RunActionsRelay,
        drafter_actions_relay: relays.DrafterActionsRelay,
        run_orchestrator_signal_relay: relays.RunOrchestratorSignalRelay,
    ) -> None:
        self._run_actions_relay = run_actions_relay
        self._drafter_actions_relay = drafter_actions_relay
        self._run_orchestrator_signal_relay = run_orchestrator_signal_relay

    async def draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        run_id = draft_stories_request.run_id
        job = draft_stories_request.job
        await self._run_actions_relay.run_keep_run(MapToKeepRunRequest(run_id, job))
        write_stories_response = await self._drafter_actions_relay.run_write_stories(MapToWriteStoriesRequest(job))
        offer_stories_response = await self._run_actions_relay.run_offer_stories(
            MapToOfferStoriesRequest(run_id, job, write_stories_response)
        )
        await_pick_stories_response = await self._run_orchestrator_signal_relay.await_pick_stories(
            MapToAwaitPickStoriesRequest(offer_stories_response)
        )
        return MapToDraftStoriesResponse(await_pick_stories_response)
