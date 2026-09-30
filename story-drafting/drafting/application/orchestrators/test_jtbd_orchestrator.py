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
        self.received: list[relays.RecordStoriesRequest] = []

    async def run_record_stories(self, record_stories_request: relays.RecordStoriesRequest) -> relays.RecordStoriesResponse:
        self.journal.append("run_record_stories")
        self.received.append(record_stories_request)
        return relays.RecordStoriesResponse(jtbd_id=record_stories_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_story_drafting_runs_its_steps_in_order_and_answers_from_the_last(self) -> None:
        journal: list[str] = []
        fake_story_actions_relay = FakeStoryActionsRelay(journal)
        fake_jtbd_actions_relay = FakeJtbdActionsRelay(journal)

        story_drafting_response = await orchestrators.JtbdOrchestrator(fake_story_actions_relay, fake_jtbd_actions_relay).story_drafting(
            relays.StoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="stories drafted for my job to be done", so_that="I can decide which to keep")
        )

        assert journal == ["run_draft_stories", "run_record_stories"]
        assert [(received.role, received.i_want, received.so_that,) for received in fake_story_actions_relay.received if isinstance(received, relays.DraftStoriesRequest)] == [("a developer", "stories drafted for my job to be done", "I can decide which to keep",)]
        assert [(received.jtbd_id, received.role, received.i_want, received.so_that, received.story_texts,) for received in fake_jtbd_actions_relay.received if isinstance(received, relays.RecordStoriesRequest)] == [("jtbd-1", "a developer", "stories drafted for my job to be done", "I can decide which to keep", (relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),),)]
        assert story_drafting_response.jtbd_id == "jtbd-1"
