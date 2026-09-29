from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.DraftJtbdRequest] = []

    async def run_draft_jtbd(self, draft_jtbd_request: relays.DraftJtbdRequest) -> relays.DraftJtbdResponse:
        self.recorded.append(draft_jtbd_request)
        return relays.DraftJtbdResponse(jtbd_id=draft_jtbd_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_arrange_drafting_runs_draft_jtbd_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.arrange_drafting(
            relays.ArrangeDraftingRequest(jtbd_id="jtbd-1", status="pending")
        )

        assert [
            (recorded.jtbd_id, recorded.status)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "pending")]

    async def test_arrange_drafting_answers_the_jtbd_id_that_draft_jtbd_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        arrange_drafting_response = await jtbd_orchestrator.arrange_drafting(
            relays.ArrangeDraftingRequest(jtbd_id="jtbd-1", status="pending")
        )

        assert arrange_drafting_response.jtbd_id == "jtbd-1"
