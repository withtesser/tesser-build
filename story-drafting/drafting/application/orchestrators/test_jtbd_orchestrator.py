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

    async def test_draft_jtbd_runs_record_jtbd_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.draft_jtbd(
            relays.DraftJtbdRequest(jtbd_id="jtbd-1", situation="working through a multi-step piece of work with an agent", motivation="the steps and checkpoints fixed in advance", outcome="step away and resume at the step we were on")
        )

        assert [
            (recorded.jtbd_id, recorded.situation, recorded.motivation, recorded.outcome)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "working through a multi-step piece of work with an agent", "the steps and checkpoints fixed in advance", "step away and resume at the step we were on")]

    async def test_draft_jtbd_answers_the_jtbd_id_that_record_jtbd_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        draft_jtbd_response = await jtbd_orchestrator.draft_jtbd(
            relays.DraftJtbdRequest(jtbd_id="jtbd-1", situation="working through a multi-step piece of work with an agent", motivation="the steps and checkpoints fixed in advance", outcome="step away and resume at the step we were on")
        )

        assert draft_jtbd_response.jtbd_id == "jtbd-1"
