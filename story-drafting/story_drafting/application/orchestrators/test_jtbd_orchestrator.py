from __future__ import annotations

import tesser.testing as ts

import story_drafting.application.orchestrators as orchestrators
import story_drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.WriteDraftsRequest] = []

    async def run_write_drafts(self, write_drafts_request: relays.WriteDraftsRequest) -> relays.WriteDraftsResponse:
        self.recorded.append(write_drafts_request)
        return relays.WriteDraftsResponse(jtbd_id=write_drafts_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_work_through_jtbd_runs_write_drafts_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", job="Design a feature, get my sign-off, then build it")
        )

        assert [
            (recorded.jtbd_id, recorded.job)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "Design a feature, get my sign-off, then build it")]

    async def test_work_through_jtbd_answers_the_jtbd_id_that_write_drafts_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        work_through_jtbd_response = await jtbd_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", job="Design a feature, get my sign-off, then build it")
        )

        assert work_through_jtbd_response.jtbd_id == "jtbd-1"
