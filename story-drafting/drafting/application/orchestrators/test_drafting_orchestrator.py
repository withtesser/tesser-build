from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeWritingActionsRelay(relays.WritingActionsRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def run_write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self._steps.append("wrote for " + write_stories_request.job)
        return relays.WriteStoriesResponse(texts=("first", "second"))


@ts.fake
class FakeDraftingActionsRelay(relays.DraftingActionsRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def run_keep_drafted_stories(
        self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest
    ) -> relays.KeepDraftedStoriesResponse:
        self._steps.append(
            "kept " + keep_drafted_stories_request.drafting_id + " " + ",".join(keep_drafted_stories_request.texts)
        )
        return relays.KeepDraftedStoriesResponse(drafting_id=keep_drafted_stories_request.drafting_id)


@ts.fake
class FakeDraftingOrchestratorSignalRelay(relays.DraftingOrchestratorSignalRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def await_pick_story(self, await_pick_story_request: relays.AwaitPickStoryRequest) -> relays.AwaitPickStoryResponse:
        self._steps.append("picked for " + await_pick_story_request.drafting_id)
        return relays.AwaitPickStoryResponse(story_id="1")


class TestDraftingOrchestrator:

    async def test_conducting_writes_the_stories_keeps_them_then_waits_for_the_pick(self) -> None:
        steps: list[str] = []

        conduct_drafting_response = await orchestrators.DraftingOrchestrator(
            FakeWritingActionsRelay(steps), FakeDraftingActionsRelay(steps), FakeDraftingOrchestratorSignalRelay(steps)
        ).conduct_drafting(relays.ConductDraftingRequest(drafting_id="d1", job="a job"))

        assert conduct_drafting_response.drafting_id == "d1"
        assert steps == ["wrote for a job", "kept d1 first,second", "picked for d1"]
