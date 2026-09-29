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
        self.conducted: list[relays.ConductRunRequest] = []

    async def run_conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.ConductRunResponse:
        self.conducted.append(conduct_run_request)
        return relays.ConductRunResponse(run_id=conduct_run_request.run_id)


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
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        return ports.LoadRunResponse(runs=(self._runs[load_run_request.run_id],))


@ts.fake
class FakeRunStore(ports.RunStore):

    def __init__(self) -> None:
        self.runs: dict[str, ports.Run] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield FakeRunRepository(self.runs)


class TestRunService:

    async def test_begin_run_conducts_the_run_under_the_run_id_its_identity_repository_issued(self) -> None:
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        run_service = application.RunService(
            fake_run_orchestrator_relay, FakeRunIdentityRepository(), FakeRunStore()
        )

        begin_run_response = await run_service.begin_run(
            client.BeginRunRequest(job="Plan a trip")
        )

        assert [
            (conducted.run_id, conducted.job)
            for conducted in fake_run_orchestrator_relay.conducted
        ] == [("run-2", "Plan a trip")]
        assert begin_run_response.run_id == "run-2"

    async def test_a_saved_run_is_read_back_by_its_run_id(self) -> None:
        fake_run_store = FakeRunStore()
        fake_run_store.runs["run-1"] = ports.Run(
            run_id="run-1", job="Plan a trip"
        )
        run_service = application.RunService(
            FakeRunOrchestratorRelay(), FakeRunIdentityRepository(), fake_run_store
        )

        get_run_response = await run_service.get_run(client.GetRunRequest(run_id="run-1"))

        assert get_run_response.run.run_id == "run-1"
        assert get_run_response.run.job == "Plan a trip"
