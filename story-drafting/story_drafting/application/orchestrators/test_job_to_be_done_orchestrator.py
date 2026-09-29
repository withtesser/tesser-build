from __future__ import annotations

import tesser.testing as ts

import story_drafting.application.orchestrators as orchestrators
import story_drafting.application.relays as relays


@ts.fake
class FakeJobToBeDoneActionsRelay(relays.JobToBeDoneActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordJtbdRequest] = []

    async def run_record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse:
        self.recorded.append(record_jtbd_request)
        return relays.RecordJtbdResponse(jtbd_id=record_jtbd_request.jtbd_id)


class TestJobToBeDoneOrchestrator:

    async def test_work_through_jtbd_runs_record_jtbd_with_the_job_to_be_done(self) -> None:
        fake_job_to_be_done_actions_relay = FakeJobToBeDoneActionsRelay()
        job_to_be_done_orchestrator = orchestrators.JobToBeDoneOrchestrator(fake_job_to_be_done_actions_relay)

        await job_to_be_done_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary")
        )

        assert [
            (recorded.jtbd_id, recorded.statement, recorded.step, recorded.draft_count, recorded.picked_draft)
            for recorded in fake_job_to_be_done_actions_relay.recorded
        ] == [("jtbd-1", "When I plan a trip I want an itinerary", "drafting", 1, "As a traveller I want an itinerary")]

    async def test_work_through_jtbd_answers_the_jtbd_id_that_record_jtbd_answered(self) -> None:
        job_to_be_done_orchestrator = orchestrators.JobToBeDoneOrchestrator(FakeJobToBeDoneActionsRelay())

        work_through_jtbd_response = await job_to_be_done_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary")
        )

        assert work_through_jtbd_response.jtbd_id == "jtbd-1"
