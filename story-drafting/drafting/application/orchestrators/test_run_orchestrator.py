from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunActionsRelay(relays.RunActionsRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def run_record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        run = record_run_request.run
        self._steps.append(f"record {run.identity} {run.stage} {len(run.stories)} {len(run.accepted_stories)}")
        return relays.RecordRunResponse(run_id=str(run.identity))


@ts.fake
class FakeStoryActionsRelay(relays.StoryActionsRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def run_write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self._steps.append(f"write {write_stories_request.job}")
        return relays.WriteStoriesResponse(stories=("a story", "another story"))


@ts.fake
class FakeRunOrchestratorSignalRelay(relays.RunOrchestratorSignalRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def await_pick_story(
        self, await_pick_story_request: relays.AwaitPickStoryRequest
    ) -> relays.AwaitPickStoryResponse:
        self._steps.append(f"await {await_pick_story_request.run_id}")
        return relays.AwaitPickStoryResponse(run_id=await_pick_story_request.run_id)


class TestRunOrchestrator:

    async def test_drafting_stories_records_the_run_writes_its_stories_records_it_awaiting_the_pick_then_waits(self) -> None:
        steps: list[str] = []
        run = domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=()))
        draft_stories_response = await orchestrators.RunOrchestrator(
            FakeRunActionsRelay(steps), FakeStoryActionsRelay(steps), FakeRunOrchestratorSignalRelay(steps)
        ).draft_stories(relays.DraftStoriesRequest(run=run))
        assert draft_stories_response.run_id == "r1"
        assert steps == [
            "record r1 drafting 0 0",
            "write ship",
            "record r1 awaiting_pick 2 0",
            "await r1",
        ]
