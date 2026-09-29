from __future__ import annotations

import tesser.testing as ts

import jtbds.application.orchestrators as orchestrators
import jtbds.application.relays as relays


@ts.fake
class FakeJobToBeDoneActionsRelay(relays.JobToBeDoneActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.InitializeJtbdRequest] = []

    async def run_initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        self.recorded.append(initialize_jtbd_request)
        return relays.InitializeJtbdResponse(jtbd_id=initialize_jtbd_request.jtbd_id)


class TestJobToBeDoneOrchestrator:

    async def test_process_jtbd_runs_initialize_jtbd_with_the_job_to_be_done(self) -> None:
        fake_job_to_be_done_actions_relay = FakeJobToBeDoneActionsRelay()
        job_to_be_done_orchestrator = orchestrators.JobToBeDoneOrchestrator(fake_job_to_be_done_actions_relay)

        await job_to_be_done_orchestrator.process_jtbd(
            relays.ProcessJtbdRequest(jtbd_id="jtbd-1", description="design new feature", status="drafting")
        )

        assert [
            (recorded.jtbd_id, recorded.description, recorded.status)
            for recorded in fake_job_to_be_done_actions_relay.recorded
        ] == [("jtbd-1", "design new feature", "drafting")]

    async def test_process_jtbd_answers_the_jtbd_id_that_initialize_jtbd_answered(self) -> None:
        job_to_be_done_orchestrator = orchestrators.JobToBeDoneOrchestrator(FakeJobToBeDoneActionsRelay())

        process_jtbd_response = await job_to_be_done_orchestrator.process_jtbd(
            relays.ProcessJtbdRequest(jtbd_id="jtbd-1", description="design new feature", status="drafting")
        )

        assert process_jtbd_response.jtbd_id == "jtbd-1"
