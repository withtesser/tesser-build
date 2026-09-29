from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.RecordJtbdRequest] = []

    async def run_record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse:
        self.recorded.append(record_jtbd_request)
        return relays.RecordJtbdResponse(jtbd_id=record_jtbd_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_work_through_jtbd_runs_record_jtbd_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were")
        )

        assert [
            (recorded.jtbd_id, recorded.situation, recorded.motivation, recorded.outcome)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "I am working through a multi-step piece of work with an agent", "the steps and my checkpoints fixed in advance", "I can step away and resume where we were")]

    async def test_work_through_jtbd_answers_the_jtbd_id_that_record_jtbd_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        work_through_jtbd_response = await jtbd_orchestrator.work_through_jtbd(
            relays.WorkThroughJtbdRequest(jtbd_id="jtbd-1", situation="I am working through a multi-step piece of work with an agent", motivation="the steps and my checkpoints fixed in advance", outcome="I can step away and resume where we were")
        )

        assert work_through_jtbd_response.jtbd_id == "jtbd-1"
