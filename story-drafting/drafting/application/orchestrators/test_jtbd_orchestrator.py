# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


@ts.fake
class FakeStoryActionsRelay(relays.StoryActionsRelay):

    def __init__(self, journal: list[str]) -> None:
        self.journal = journal
        self.received: list[relays.DraftStoriesRequest] = []

    async def run_draft_stories(self, draft_stories_request: relays.DraftStoriesRequest) -> relays.DraftStoriesResponse:
        self.journal.append("run_draft_stories")
        self.received.append(draft_stories_request)
        return relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),))


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self, journal: list[str]) -> None:
        self.journal = journal
        self.received: list[relays.RecordDraftedStoriesRequest] = []

    async def run_record_drafted_stories(self, record_drafted_stories_request: relays.RecordDraftedStoriesRequest) -> relays.RecordDraftedStoriesResponse:
        self.journal.append("run_record_drafted_stories")
        self.received.append(record_drafted_stories_request)
        return relays.RecordDraftedStoriesResponse(jtbd_id=record_drafted_stories_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_story_drafting_runs_its_steps_in_order_and_answers_from_the_last(self) -> None:
        journal: list[str] = []
        fake_story_actions_relay = FakeStoryActionsRelay(journal)
        fake_jtbd_actions_relay = FakeJtbdActionsRelay(journal)

        story_drafting_response = await orchestrators.JtbdOrchestrator(fake_story_actions_relay, fake_jtbd_actions_relay).story_drafting(
            relays.StoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back")
        )

        assert journal == ["run_draft_stories", "run_record_drafted_stories"]
        assert [(received.jtbd_id, received.role, received.i_want, received.so_that,) for received in fake_story_actions_relay.received if isinstance(received, relays.DraftStoriesRequest)] == [("jtbd-1", "a developer", "my checkpoints fixed in advance", "I can step away and come back",)]
        assert [(received.jtbd_id, received.role, received.i_want, received.so_that, received.story_texts,) for received in fake_jtbd_actions_relay.received if isinstance(received, relays.RecordDraftedStoriesRequest)] == [("jtbd-1", "a developer", "my checkpoints fixed in advance", "I can step away and come back", (relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),),)]
        assert story_drafting_response.jtbd_id == "jtbd-1"
