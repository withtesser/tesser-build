from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client


@ts.fake
class FakeRunOrchestratorRelay(relays.RunOrchestratorRelay):

    def __init__(self) -> None:
        self.started: list[relays.DraftStoriesRequest] = []

    async def start_draft_stories(
        self, draft_stories_request: relays.DraftStoriesRequest
    ) -> relays.StartDraftStoriesResponse:
        self.started.append(draft_stories_request)
        return relays.StartDraftStoriesResponse(run_id=draft_stories_request.run_id)


@ts.fake
class FakeRunIdentityRepository(ports.RunIdentityRepository):

    async def issue_run_id(self, issue_run_id_request: ports.IssueRunIdRequest) -> ports.IssueRunIdResponse:
        return ports.IssueRunIdResponse(run_id="run-2")


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self, runs: dict[str, ports.Run]) -> None:
        self._runs = runs

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self._runs[save_run_request.run_id] = ports.Run(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            stage=save_run_request.stage,
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        if load_run_request.run_id not in self._runs:
            return ports.LoadRunResponse(runs=())
        return ports.LoadRunResponse(runs=(self._runs[load_run_request.run_id],))


@ts.fake
class FakeRunStore(ports.RunStore):

    def __init__(self) -> None:
        self.runs: dict[str, ports.Run] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield FakeRunRepository(self.runs)


class TestRunService:

    async def test_open_run_starts_drafting_stories_for_the_run_its_identity_repository_issued(self) -> None:
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        run_service = application.RunService(
            fake_run_orchestrator_relay, FakeRunIdentityRepository(), FakeRunStore()
        )

        open_run_response = await run_service.open_run(client.OpenRunRequest(job="plan a migration"))

        assert [
            (started.run_id, started.job, started.stage) for started in fake_run_orchestrator_relay.started
        ] == [("run-2", "plan a migration", "drafting")]
        assert open_run_response.run_id == "run-2"

    async def test_a_saved_run_is_read_back_by_its_run_id(self) -> None:
        fake_run_store = FakeRunStore()
        fake_run_store.runs["run-1"] = ports.Run(run_id="run-1", job="plan a migration", stage="drafting")
        run_service = application.RunService(
            FakeRunOrchestratorRelay(), FakeRunIdentityRepository(), fake_run_store
        )

        get_run_response = await run_service.get_run(client.GetRunRequest(run_id="run-1"))

        assert [(run.run_id, run.job, run.stage) for run in get_run_response.runs] == [
            ("run-1", "plan a migration", "drafting")
        ]

    async def test_a_run_never_saved_reads_back_as_no_run(self) -> None:
        run_service = application.RunService(
            FakeRunOrchestratorRelay(), FakeRunIdentityRepository(), FakeRunStore()
        )

        get_run_response = await run_service.get_run(client.GetRunRequest(run_id="run-9"))

        assert get_run_response.runs == ()
