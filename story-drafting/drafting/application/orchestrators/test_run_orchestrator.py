from __future__ import annotations

import pytest
import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays
import tesser.errors as errors


@ts.fake
class FakeRunActionsRelay(relays.RunActionsRelay):

    def __init__(self, steps: list[str]) -> None:
        self.recorded: list[relays.RecordRunRequest] = []
        self._steps = steps

    async def run_record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append(record_run_request)
        self._steps.append("recorded " + record_run_request.stage)
        return relays.RecordRunResponse(run_id=record_run_request.run_id)


@ts.fake
class FakeStoryWritingActionsRelay(relays.StoryWritingActionsRelay):

    def __init__(self, steps: list[str], stories: tuple[str, ...]) -> None:
        self._steps = steps
        self._stories = stories

    async def run_write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        self._steps.append("wrote stories for " + write_stories_request.job)
        return relays.WriteStoriesResponse(stories=self._stories)


@ts.fake
class FakeRunOrchestratorSignalRelay(relays.RunOrchestratorSignalRelay):

    def __init__(self, steps: list[str]) -> None:
        self._steps = steps

    async def await_pick_stories(
        self, await_pick_stories_request: relays.AwaitPickStoriesRequest
    ) -> relays.AwaitPickStoriesResponse:
        self._steps.append("awaited the pick for " + await_pick_stories_request.run_id)
        return relays.AwaitPickStoriesResponse(stories=())


class TestRunOrchestrator:

    async def test_drafting_records_the_run_writes_its_stories_records_them_then_awaits_the_pick(self) -> None:
        steps: list[str] = []
        run_orchestrator = orchestrators.RunOrchestrator(
            FakeRunActionsRelay(steps),
            FakeStoryWritingActionsRelay(steps, ("As a developer, I want a plan",)),
            FakeRunOrchestratorSignalRelay(steps),
        )

        await run_orchestrator.draft_stories(
            relays.DraftStoriesRequest(run_id="run-1", job="plan a migration", stage="drafting")
        )

        assert steps == [
            "recorded drafting",
            "wrote stories for plan a migration",
            "recorded awaiting_pick",
            "awaited the pick for run-1",
        ]

    async def test_the_run_recorded_before_the_pick_holds_the_drafted_stories_and_none_accepted(self) -> None:
        fake_run_actions_relay = FakeRunActionsRelay([])
        run_orchestrator = orchestrators.RunOrchestrator(
            fake_run_actions_relay,
            FakeStoryWritingActionsRelay([], ("As a developer, I want a plan", "As a developer, I want a review")),
            FakeRunOrchestratorSignalRelay([]),
        )

        await run_orchestrator.draft_stories(
            relays.DraftStoriesRequest(run_id="run-1", job="plan a migration", stage="drafting")
        )

        assert [
            (recorded.stage, recorded.stories, recorded.accepted_stories) for recorded in fake_run_actions_relay.recorded
        ][-1] == ("awaiting_pick", ("As a developer, I want a plan", "As a developer, I want a review"), ())

    async def test_drafting_that_writes_no_stories_never_reaches_the_pick(self) -> None:
        steps: list[str] = []
        run_orchestrator = orchestrators.RunOrchestrator(
            FakeRunActionsRelay(steps), FakeStoryWritingActionsRelay(steps, ()), FakeRunOrchestratorSignalRelay(steps)
        )

        with pytest.raises(errors.DomainError):
            await run_orchestrator.draft_stories(
                relays.DraftStoriesRequest(run_id="run-1", job="plan a migration", stage="drafting")
            )

        assert steps == ["recorded drafting", "wrote stories for plan a migration"]

    async def test_draft_stories_answers_the_run_id_that_record_run_answered(self) -> None:
        run_orchestrator = orchestrators.RunOrchestrator(
            FakeRunActionsRelay([]),
            FakeStoryWritingActionsRelay([], ("As a developer, I want a plan",)),
            FakeRunOrchestratorSignalRelay([]),
        )

        draft_stories_response = await run_orchestrator.draft_stories(
            relays.DraftStoriesRequest(run_id="run-1", job="plan a migration", stage="drafting")
        )

        assert draft_stories_response.run_id == "run-1"
