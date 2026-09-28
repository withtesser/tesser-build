from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunActionsRelay(relays.RunActionsRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def run_keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
        self._steps.append(f"kept {keep_run_request.run_id} for {keep_run_request.job}")
        return relays.KeepRunResponse(run_id=keep_run_request.run_id)

    async def run_offer_stories(self, offer_stories_request: relays.OfferStoriesRequest) -> relays.OfferStoriesResponse:
        self._steps.append(f"offered {offer_stories_request.run_id} {list(offer_stories_request.stories)}")
        return relays.OfferStoriesResponse(run_id=offer_stories_request.run_id)


@ts.fake
class FakeDrafterActionsRelay(relays.DrafterActionsRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def run_write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self._steps.append(f"wrote stories for {write_stories_request.job}")
        return relays.WriteStoriesResponse(stories=("a story", "another story"))


@ts.fake
class FakeRunOrchestratorSignalRelay(relays.RunOrchestratorSignalRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def await_pick_stories(
        self, await_pick_stories_request: relays.AwaitPickStoriesRequest
    ) -> relays.AwaitPickStoriesResponse:
        self._steps.append(f"awaited the pick for {await_pick_stories_request.run_id}")
        return relays.AwaitPickStoriesResponse(run_id=await_pick_stories_request.run_id)


class TestRunOrchestrator:

    async def test_drafting_keeps_the_run_drafts_offers_the_stories_then_waits_for_the_pick(self) -> None:
        steps: list[str] = []
        draft_stories_response = await orchestrators.RunOrchestrator(
            FakeRunActionsRelay(steps), FakeDrafterActionsRelay(steps), FakeRunOrchestratorSignalRelay(steps)
        ).draft_stories(relays.DraftStoriesRequest(run_id=domain.RunId("r1"), job=domain.Job("a job")))
        assert draft_stories_response.run_id == "r1"
        assert steps == [
            "kept r1 for a job",
            "wrote stories for a job",
            "offered r1 ['a story', 'another story']",
            "awaited the pick for r1",
        ]
