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
        return relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="I see it drafting"),))


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

    async def test_conduct_story_drafting_runs_its_steps_in_order_and_answers_from_the_last(self) -> None:
        journal: list[str] = []
        fake_story_actions_relay = FakeStoryActionsRelay(journal)
        fake_jtbd_actions_relay = FakeJtbdActionsRelay(journal)

        conduct_story_drafting_response = await orchestrators.JtbdOrchestrator(fake_story_actions_relay, fake_jtbd_actions_relay).conduct_story_drafting(
            relays.ConductStoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="stories drafted for my work", so_that="I can accept the ones I keep")
        )

        assert journal == ["run_draft_stories", "run_record_stories"]
        assert [(received.jtbd_id, received.role, received.i_want, received.so_that,) for received in fake_story_actions_relay.received if isinstance(received, relays.DraftStoriesRequest)] == [("jtbd-1", "a developer", "stories drafted for my work", "I can accept the ones I keep",)]
        assert [(received.jtbd_id, received.role, received.i_want, received.so_that, received.story_texts,) for received in fake_jtbd_actions_relay.received if isinstance(received, relays.RecordStoriesRequest)] == [("jtbd-1", "a developer", "stories drafted for my work", "I can accept the ones I keep", (relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="I see it drafting"),),)]
        assert conduct_story_drafting_response.jtbd_id == "jtbd-1"
