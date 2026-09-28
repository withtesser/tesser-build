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
class FakeRunOrchestratorRelay(relays.RunOrchestratorRelay):

    def __init__(self) -> None:
        self.started: list[relays.ConductRunRequest] = []

    async def start_conduct_run(self, conduct_run_request: relays.ConductRunRequest) -> relays.StartConductRunResponse:
        self.started.append(conduct_run_request)
        return relays.StartConductRunResponse(run_id=conduct_run_request.run_id)


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self, runs: dict[str, ports.Run]) -> None:
        self._runs = runs

    async def issue_run_id(self, issue_run_id_request: ports.IssueRunIdRequest) -> ports.IssueRunIdResponse:
        return ports.IssueRunIdResponse(run_id="issued-1")

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self._runs[save_run_request.run_id] = ports.Run(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            step=save_run_request.step,
            drafted_stories=save_run_request.drafted_stories,
            accepted_stories=save_run_request.accepted_stories,
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        if load_run_request.run_id not in self._runs:
            return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.NOT_FOUND, runs=())
        return ports.LoadRunResponse(outcome=ports.LoadRunOutcome.FOUND, runs=(self._runs[load_run_request.run_id],))


@ts.fake
class FakeRunStore(ports.RunStore):

    def __init__(self) -> None:
        self.runs: dict[str, ports.Run] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield FakeRunRepository(self.runs)


class TestRunService:

    async def test_opening_a_run_keeps_it_and_starts_conducting_it(self) -> None:
        fake_run_store = FakeRunStore()
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        run_service = application.RunService(fake_run_store, fake_run_orchestrator_relay)

        open_run_response = await run_service.open_run(client.OpenRunRequest(job=" ship a release "))

        assert open_run_response.run_id == "issued-1"
        assert [(started.run_id, started.job) for started in fake_run_orchestrator_relay.started] == [
            ("issued-1", "ship a release")
        ]
        assert fake_run_store.runs["issued-1"].step == "drafting"

    async def test_an_opened_run_is_read_back_by_its_id(self) -> None:
        run_service = application.RunService(FakeRunStore(), FakeRunOrchestratorRelay())
        open_run_response = await run_service.open_run(client.OpenRunRequest(job="ship a release"))

        get_run_response = await run_service.get_run(client.GetRunRequest(run_id=open_run_response.run_id))

        run = get_run_response.run
        assert (run.run_id, run.job, run.step, run.drafted_stories, run.accepted_stories) == (
            "issued-1",
            "ship a release",
            "drafting",
            (),
            (),
        )

    async def test_a_job_that_says_nothing_is_rejected_and_nothing_starts(self) -> None:
        fake_run_orchestrator_relay = FakeRunOrchestratorRelay()
        run_service = application.RunService(FakeRunStore(), fake_run_orchestrator_relay)

        with pytest.raises(client.RunRejected) as raised:
            await run_service.open_run(client.OpenRunRequest(job="  "))

        assert raised.value.code == "empty_job"
        assert fake_run_orchestrator_relay.started == []

    async def test_a_run_that_was_never_opened_is_not_found(self) -> None:
        run_service = application.RunService(FakeRunStore(), FakeRunOrchestratorRelay())

        with pytest.raises(client.RunNotFound) as raised:
            await run_service.get_run(client.GetRunRequest(run_id="never"))

        assert str(raised.value) == "no run 'never'"
