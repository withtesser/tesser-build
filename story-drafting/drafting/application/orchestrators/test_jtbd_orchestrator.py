from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordSubmissionRequest] = []

    async def run_record_submission(self, record_submission_request: relays.RecordSubmissionRequest) -> relays.RecordSubmissionResponse:
        self.recorded.append(record_submission_request)
        return relays.RecordSubmissionResponse(jtbd_id=record_submission_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_work_through_jtbd_runs_record_submission_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", job="Design a login page then build it")
        )

        assert [
            (recorded.jtbd_id, recorded.job)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "Design a login page then build it")]

    async def test_work_through_jtbd_answers_the_jtbd_id_that_record_submission_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        work_through_jtbd_response = await jtbd_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", job="Design a login page then build it")
        )

        assert work_through_jtbd_response.jtbd_id == "jtbd-1"
