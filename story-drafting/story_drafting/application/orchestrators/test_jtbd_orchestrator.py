from __future__ import annotations

import tesser.testing as ts

import story_drafting.application.orchestrators as orchestrators
import story_drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.InitializeJtbdRequest] = []

    async def run_initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        self.recorded.append(initialize_jtbd_request)
        return relays.InitializeJtbdResponse(jtbd_id=initialize_jtbd_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_conduct_drafting_runs_initialize_jtbd_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.conduct_drafting(
            relays.ConductDraftingRequest(jtbd_id="jtbd-1", status="drafting")
        )

        assert [
            (recorded.jtbd_id, recorded.status)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "drafting")]

    async def test_conduct_drafting_answers_the_jtbd_id_that_initialize_jtbd_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        conduct_drafting_response = await jtbd_orchestrator.conduct_drafting(
            relays.ConductDraftingRequest(jtbd_id="jtbd-1", status="drafting")
        )

        assert conduct_drafting_response.jtbd_id == "jtbd-1"
