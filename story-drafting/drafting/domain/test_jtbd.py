# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=(domain.StorySpec(given="a job to be done", when="I submit it", then="it is drafting its stories", state=domain.StoryState.DRAFTED),))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == "jtbd-1"
        assert str(jtbd.role) == "a developer"
        assert str(jtbd.i_want) == "my steps fixed in advance"
        assert str(jtbd.so_that) == "I can step away"
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a job to be done", "I submit it", "it is drafting its stories", "drafted",)]

    def test_a_jtbd_answers_draft_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=()))

        draft_stories_outcome = jtbd.draft_stories(domain.DraftStoriesSpec())

        assert isinstance(draft_stories_outcome, domain.DraftStoriesOutcome)

    def test_a_jtbd_reads_its_status_as_one_of_its_values(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=()))

        assert str(jtbd.status) in [jtbd_status.value for jtbd_status in domain.JtbdStatus]

    def test_a_jtbd_with_no_stories_is_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=()))

        status = jtbd.status

        assert str(status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_a_jtbd_whose_stories_are_drafted_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=()))

        jtbd.draft_stories(domain.DraftStoriesSpec())

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_drafting_stories_writes_at_least_one_drafted_story_with_a_given_a_when_and_a_then(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=()))

        jtbd.draft_stories(domain.DraftStoriesSpec())

        assert len(jtbd.stories) >= 1
        assert all(str(story.given) and str(story.when) and str(story.then) and str(story.state) == domain.StoryState.DRAFTED.value for story in jtbd.stories)

    def test_drafted_stories_are_written_from_the_jtbd(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away", stories=()))

        jtbd.draft_stories(domain.DraftStoriesSpec())

        assert [(str(story.given), str(story.when), str(story.then)) for story in jtbd.stories] == [("I am a developer", "I get my steps fixed in advance", "I can see that I can step away")]
