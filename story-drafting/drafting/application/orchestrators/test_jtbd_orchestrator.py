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
        return relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="it is drafting"),))


@ts.fake
class FakeJtbdActionsRelay(relays.JtbdActionsRelay):

    def __init__(self, journal: list[str]) -> None:
        self.journal = journal
        self.received: list[relays.RecordStoriesRequest] = []

    async def run_record_stories(self, record_stories_request: relays.RecordStoriesRequest) -> relays.RecordStoriesResponse:
        self.journal.append("run_record_stories")
        self.received.append(record_stories_request)
        return relays.RecordStoriesResponse(jtbd_id=record_stories_request.jtbd_id)


@ts.fake
class FakeJtbdOrchestratorSignalRelay(relays.JtbdOrchestratorSignalRelay):

    def __init__(self, journal: list[str]) -> None:
        self.journal = journal
        self.received: list[relays.AwaitAcceptStoriesRequest] = []

    async def await_accept_stories(self, await_accept_stories_request: relays.AwaitAcceptStoriesRequest) -> relays.AwaitAcceptStoriesResponse:
        self.journal.append("await_accept_stories")
        self.received.append(await_accept_stories_request)
        return relays.AwaitAcceptStoriesResponse(jtbd_id=await_accept_stories_request.jtbd_id)


class TestJtbdOrchestrator:

    async def test_conduct_story_drafting_runs_its_steps_in_order_and_answers_from_the_last(self) -> None:
        journal: list[str] = []
        fake_story_actions_relay = FakeStoryActionsRelay(journal)
        fake_jtbd_actions_relay = FakeJtbdActionsRelay(journal)
        fake_jtbd_orchestrator_signal_relay = FakeJtbdOrchestratorSignalRelay(journal)

        conduct_story_drafting_response = await orchestrators.JtbdOrchestrator(fake_story_actions_relay, fake_jtbd_actions_relay, fake_jtbd_orchestrator_signal_relay).conduct_story_drafting(
            relays.ConductStoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away and return")
        )

        assert journal == ["run_draft_stories", "run_record_stories", "await_accept_stories"]
        assert [(received.role, received.i_want, received.so_that,) for received in fake_story_actions_relay.received if isinstance(received, relays.DraftStoriesRequest)] == [("a developer", "my steps fixed in advance", "I can step away and return",)]
        assert [(received.jtbd_id, received.role, received.i_want, received.so_that, received.story_texts,) for received in fake_jtbd_actions_relay.received if isinstance(received, relays.RecordStoriesRequest)] == [("jtbd-1", "a developer", "my steps fixed in advance", "I can step away and return", (relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting"),),)]
        assert [(received.jtbd_id,) for received in fake_jtbd_orchestrator_signal_relay.received if isinstance(received, relays.AwaitAcceptStoriesRequest)] == [("jtbd-1",)]
        assert conduct_story_drafting_response.jtbd_id == "jtbd-1"
