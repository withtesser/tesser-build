from __future__ import annotations

import pytest

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self) -> None:
        self.runs: dict[str, ports.RunRecord] = {}

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self.runs[save_run_request.run_id] = ports.RunRecord(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            stage=save_run_request.stage,
            stories=(),
            accepted_stories=(),
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def get_run(self, get_run_request: ports.GetRunRequest) -> ports.GetRunResponse:
        if get_run_request.run_id not in self.runs:
            return ports.GetRunResponse(outcome=ports.GetRunOutcome.NOT_FOUND, runs=())
        return ports.GetRunResponse(outcome=ports.GetRunOutcome.FOUND, runs=(self.runs[get_run_request.run_id],))


@ts.fake
class FakeRunOrchestratorRelay(relays.RunOrchestratorRelay):

    def __init__(self) -> None:
        self.started: list[tuple[str, str]] = []

    async def start_draft_stories(
        self, draft_stories_request: relays.DraftStoriesRequest
    ) -> relays.StartDraftStoriesResponse:
        self.started.append((str(draft_stories_request.run_id), str(draft_stories_request.job)))
        return relays.StartDraftStoriesResponse(run_id=str(draft_stories_request.run_id))


class TestRunService:

    async def test_beginning_a_run_starts_drafting_stories_for_its_job(self) -> None:
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        begin_run_response = await application.RunService(FakeRunRepository(), fake_run_orchestrator_relay).begin_run(
            client.BeginRunRequest(run_id="r1", job="a job")
        )
        assert begin_run_response.run_id == "r1"
        assert fake_run_orchestrator_relay.started == [("r1", "a job")]

    async def test_a_run_with_a_blank_job_is_rejected_and_never_started(self) -> None:
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        with pytest.raises(client.RunRejected) as rejected:
            await application.RunService(FakeRunRepository(), fake_run_orchestrator_relay).begin_run(
                client.BeginRunRequest(run_id="r1", job=" ")
            )
        assert rejected.value.code == "empty_job"
        assert fake_run_orchestrator_relay.started == []

    async def test_a_kept_run_is_read_back_as_it_was_kept(self) -> None:
        fake_run_repository = FakeRunRepository()
        await fake_run_repository.save_run(ports.SaveRunRequest(run_id="r1", job="a job", stage="drafting"))
        get_run_response = await application.RunService(fake_run_repository, FakeRunOrchestratorRelay()).get_run(
            client.GetRunRequest(run_id="r1")
        )
        assert (get_run_response.run_id, get_run_response.job, get_run_response.stage) == ("r1", "a job", "drafting")
        assert get_run_response.stories == ()
        assert get_run_response.accepted_stories == ()

    async def test_a_run_never_kept_is_not_found(self) -> None:
        with pytest.raises(client.RunNotFound):
            await application.RunService(FakeRunRepository(), FakeRunOrchestratorRelay()).get_run(
                client.GetRunRequest(run_id="r1")
            )

    async def test_reading_an_empty_run_id_is_rejected(self) -> None:
        with pytest.raises(client.RunRejected) as rejected:
            await application.RunService(FakeRunRepository(), FakeRunOrchestratorRelay()).get_run(
                client.GetRunRequest(run_id="")
            )
        assert rejected.value.code == "empty_run_id"
