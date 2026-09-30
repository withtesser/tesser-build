# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self, journal: list[str]) -> None:
        self.journal = journal
        self.received: list[relays.DraftStoriesRequest] = []

    async def run_draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self.journal.append("run_draft_stories")
        self.received.append(draft_stories_request)
        return relays.DraftStoriesResponse(jtbd_id=draft_stories_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_story_drafting_runs_its_steps_in_order_and_answers_from_the_last(self) -> None:
        journal: list[str] = []
        fake_jtbd_actions_relay = FakeJtbdActionsRelay(journal)

        story_drafting_response = await orchestrators.JtbdOrchestrator(fake_jtbd_actions_relay).story_drafting(
            relays.StoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away")
        )

        assert journal == ["run_draft_stories"]
        assert [(received.jtbd_id, received.role, received.i_want, received.so_that,) for received in fake_jtbd_actions_relay.received if isinstance(received, relays.DraftStoriesRequest)] == [("jtbd-1", "a developer", "my steps fixed in advance", "I can step away",)]
        assert story_drafting_response.jtbd_id == "jtbd-1"
