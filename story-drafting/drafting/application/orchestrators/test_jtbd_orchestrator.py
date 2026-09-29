from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[relays.WriteDraftsRequest] = []

    async def run_write_drafts(self, write_drafts_request: relays.WriteDraftsRequest) -> relays.WriteDraftsResponse:
        self.recorded.append(write_drafts_request)
        return relays.WriteDraftsResponse(jtbd_id=write_drafts_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_draft_stories_runs_write_drafts_with_the_jtbd(self) -> None:
        fake_jtbd_actions_relay = FakeJtbdActionsRelay()
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay)

        await jtbd_orchestrator.draft_stories(
            relays.DraftStoriesRequest(jtbd_id="jtbd-1", job="design then build")
        )

        assert [
            (recorded.jtbd_id, recorded.job)
            for recorded in fake_jtbd_actions_relay.recorded
        ] == [("jtbd-1", "design then build")]

    async def test_draft_stories_answers_the_jtbd_id_that_write_drafts_answered(self) -> None:
        jtbd_orchestrator = orchestrators.JtbdOrchestrator(FakeJtbdActionsRelay())

        draft_stories_response = await jtbd_orchestrator.draft_stories(
            relays.DraftStoriesRequest(jtbd_id="jtbd-1", job="design then build")
        )

        assert draft_stories_response.jtbd_id == "jtbd-1"
