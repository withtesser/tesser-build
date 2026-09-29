from __future__ import annotations

import tesser.testing as ts

import story_drafting.application.orchestrators as orchestrators
import story_drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.BeginDraftingRequest] = []

    async def run_begin_drafting(self, begin_drafting_request: relays.BeginDraftingRequest) -> relays.BeginDraftingResponse:
        self.recorded.append(begin_drafting_request)
        return relays.BeginDraftingResponse(jtbd_id=begin_drafting_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_begin_draft_process_runs_begin_drafting_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.begin_draft_process(
            relays.BeginDraftProcessRequest(jtbd_id="jtbd-1", status="drafting")
        )

        assert [
            (recorded.jtbd_id, recorded.status)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "drafting")]

    async def test_begin_draft_process_answers_the_jtbd_id_that_begin_drafting_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        begin_draft_process_response = await jtbd_orchestrator.begin_draft_process(
            relays.BeginDraftProcessRequest(jtbd_id="jtbd-1", status="drafting")
        )

        assert begin_draft_process_response.jtbd_id == "jtbd-1"
