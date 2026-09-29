from __future__ import annotations

import contextlib
import typing

import pytest
import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self, runs: tuple[ports.RunRecord, ...]) -> None:
        self._runs = runs

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        runs = tuple(run for run in self._runs if run.run_id == load_run_request.run_id)
        if runs:
            return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.FOUND, runs=runs)
        return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.NOT_FOUND, runs=())


@ts.fake
class FakeRunStore(ports.RunStore):

    def __init__(self, fake_run_repository: FakeRunRepository) -> None:
        self._fake_run_repository = fake_run_repository

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield self._fake_run_repository


@ts.fake
class FakeRunOrchestratorRelay(relays.RunOrchestratorRelay):

    def __init__(self) -> None:
        self.started: list[tuple[str, str, str]] = []

    async def start_draft_stories(
        self, draft_stories_request: relays.DraftStoriesRequest
    ) -> relays.StartDraftStoriesResponse:
        run = draft_stories_request.run
        self.started.append((str(run.identity), str(run.job), str(run.stage)))
        return relays.StartDraftStoriesResponse(run_id=str(run.identity))


class TestDraftingService:

    async def test_opening_a_run_starts_the_orchestrator_on_a_run_that_is_drafting(self) -> None:
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        drafting_service = application.DraftingService(FakeRunStore(FakeRunRepository(())), fake_run_orchestrator_relay)
        open_run_response = await drafting_service.open_run(client.OpenRunRequest(run_id="r1", job="ship"))
        assert open_run_response.run_id == "r1"
        assert fake_run_orchestrator_relay.started == [("r1", "ship", "drafting")]

    async def test_a_run_the_domain_refuses_is_rejected_and_nothing_starts(self) -> None:
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        drafting_service = application.DraftingService(FakeRunStore(FakeRunRepository(())), fake_run_orchestrator_relay)
        with pytest.raises(client.RunRejected) as excinfo:
            await drafting_service.open_run(client.OpenRunRequest(run_id="r1", job=" "))
        assert excinfo.value.code == "empty_job"
        assert fake_run_orchestrator_relay.started == []

    async def test_a_recorded_run_is_read_back_as_it_was_recorded(self) -> None:
        run_record = ports.RunRecord(
            run_id="r1", job="ship", stage="awaiting_pick", stories=("a story",), accepted_stories=()
        )
        drafting_service = application.DraftingService(
            FakeRunStore(FakeRunRepository((run_record,))), FakeRunOrchestratorRelay()
        )
        get_run_response = await drafting_service.get_run(client.GetRunRequest(run_id="r1"))
        assert (
            get_run_response.run_id,
            get_run_response.job,
            get_run_response.stage,
            get_run_response.stories,
            get_run_response.accepted_stories,
        ) == ("r1", "ship", "awaiting_pick", ("a story",), ())

    async def test_a_run_never_recorded_is_not_found(self) -> None:
        drafting_service = application.DraftingService(FakeRunStore(FakeRunRepository(())), FakeRunOrchestratorRelay())
        with pytest.raises(client.RunNotFound):
            await drafting_service.get_run(client.GetRunRequest(run_id="r1"))

    async def test_reading_an_invalid_run_id_is_rejected(self) -> None:
        drafting_service = application.DraftingService(FakeRunStore(FakeRunRepository(())), FakeRunOrchestratorRelay())
        with pytest.raises(client.RunRejected):
            await drafting_service.get_run(client.GetRunRequest(run_id=".."))
