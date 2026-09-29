from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeRunActionsRelay(relays.RunActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordRunRequest] = []

    async def run_record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append(record_run_request)
        return relays.RecordRunResponse(run_id=record_run_request.run_id)


class TestRunOrchestrator:

    async def test_conduct_run_runs_record_run_with_the_run(self) -> None:
        fake_run_actions_relay = FakeRunActionsRelay()
        run_orchestrator = orchestrators.RunOrchestrator(fake_run_actions_relay)

        await run_orchestrator.conduct_run(
            relays.ConductRunRequest(run_id="run-1", job="Plan a trip")
        )

        assert [
            (recorded.run_id, recorded.job)
            for recorded in fake_run_actions_relay.recorded
        ] == [("run-1", "Plan a trip")]

    async def test_conduct_run_answers_the_run_id_that_record_run_answered(self) -> None:
        run_orchestrator = orchestrators.RunOrchestrator(FakeRunActionsRelay())

        conduct_run_response = await run_orchestrator.conduct_run(
            relays.ConductRunRequest(run_id="run-1", job="Plan a trip")
        )

        assert conduct_run_response.run_id == "run-1"
