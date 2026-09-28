from __future__ import annotations

import pytest

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays
import tesser.errors as errors


@ts.fake
class FakeDraftingActionsRelay(relays.DraftingActionsRelay):

    def __init__(self, stories: tuple[str, ...], happened: list[str]) -> None:
        self._stories = stories
        self._happened = happened

    async def run_draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self._happened.append(f"draft {draft_stories_request.run_id}: {draft_stories_request.job}")
        return relays.DraftStoriesResponse(stories=self._stories)


@ts.fake
class FakeRunActionsRelay(relays.RunActionsRelay):

    def __init__(self, happened: list[str]) -> None:
        self._happened = happened
        self.recorded: list[relays.RecordRunRequest] = []

    async def run_record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self._happened.append(f"record {record_run_request.run_id}")
        self.recorded.append(record_run_request)
        return relays.RecordRunResponse(run_id=record_run_request.run_id)


@ts.fake
class FakeRunOrchestratorSignalRelay(relays.RunOrchestratorSignalRelay):

    def __init__(self, happened: list[str]) -> None:
        self._happened = happened

    async def await_pick_stories(
        self, await_pick_stories_request: relays.AwaitPickStoriesRequest
    ) -> relays.AwaitPickStoriesResponse:
        self._happened.append(f"await pick stories {await_pick_stories_request.run_id}")
        return relays.AwaitPickStoriesResponse(run_id=await_pick_stories_request.run_id)


class TestRunOrchestrator:

    async def test_a_run_drafts_then_records_its_drafts_then_waits_for_the_pick(self) -> None:
        happened: list[str] = []
        run_orchestrator = orchestrators.RunOrchestrator(
            FakeDraftingActionsRelay(("first",), happened),
            FakeRunActionsRelay(happened),
            FakeRunOrchestratorSignalRelay(happened),
        )

        await run_orchestrator.conduct_run(relays.ConductRunRequest(run_id="r1", job="ship a release"))

        assert happened == ["draft r1: ship a release", "record r1", "await pick stories r1"]

    async def test_the_recorded_run_awaits_the_pick_with_its_drafted_stories_and_none_accepted(self) -> None:
        happened: list[str] = []
        fake_run_actions_relay = FakeRunActionsRelay(happened)
        run_orchestrator = orchestrators.RunOrchestrator(
            FakeDraftingActionsRelay(("first", "second"), happened),
            fake_run_actions_relay,
            FakeRunOrchestratorSignalRelay(happened),
        )

        await run_orchestrator.conduct_run(relays.ConductRunRequest(run_id="r1", job="ship a release"))

        assert [
            (
                record_run_request.run_id,
                record_run_request.job,
                record_run_request.step,
                record_run_request.drafted_stories,
                record_run_request.accepted_stories,
            )
            for record_run_request in fake_run_actions_relay.recorded
        ] == [("r1", "ship a release", "awaiting_pick", ("first", "second"), ())]

    async def test_conducting_a_run_answers_its_run_id_once_the_pick_is_in(self) -> None:
        happened: list[str] = []
        run_orchestrator = orchestrators.RunOrchestrator(
            FakeDraftingActionsRelay(("first",), happened),
            FakeRunActionsRelay(happened),
            FakeRunOrchestratorSignalRelay(happened),
        )

        conduct_run_response = await run_orchestrator.conduct_run(
            relays.ConductRunRequest(run_id="r1", job="ship a release")
        )

        assert conduct_run_response.run_id == "r1"

    async def test_a_draft_with_no_stories_is_refused_before_anything_is_recorded(self) -> None:
        happened: list[str] = []
        run_orchestrator = orchestrators.RunOrchestrator(
            FakeDraftingActionsRelay((), happened),
            FakeRunActionsRelay(happened),
            FakeRunOrchestratorSignalRelay(happened),
        )

        with pytest.raises(errors.DomainError):
            await run_orchestrator.conduct_run(relays.ConductRunRequest(run_id="r1", job="ship a release"))

        assert happened == ["draft r1: ship a release"]
