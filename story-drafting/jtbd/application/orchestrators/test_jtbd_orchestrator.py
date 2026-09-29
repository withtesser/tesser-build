from __future__ import annotations

import tesser.testing as ts

import jtbd.application.orchestrators as orchestrators
import jtbd.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.MarkJtbdDraftingRequest] = []

    async def run_mark_jtbd_drafting(self, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest) -> relays.MarkJtbdDraftingResponse:
        self.recorded.append(mark_jtbd_drafting_request)
        return relays.MarkJtbdDraftingResponse(jtbd_id=mark_jtbd_drafting_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_draft_for_jtbd_runs_mark_jtbd_drafting_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.draft_for_jtbd(
            relays.DraftForJtbdRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")
        )

        assert [
            (recorded.jtbd_id, recorded.description, recorded.status)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "design-feature", "drafting")]

    async def test_draft_for_jtbd_answers_the_jtbd_id_that_mark_jtbd_drafting_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        draft_for_jtbd_response = await jtbd_orchestrator.draft_for_jtbd(
            relays.DraftForJtbdRequest(jtbd_id="jtbd-1", description="design-feature", status="drafting")
        )

        assert draft_for_jtbd_response.jtbd_id == "jtbd-1"
