# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import pytest

import tesser.errors as errors

import drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=(domain.StorySpec(given="a job to be done", when="I submit it", then="I can come back to it", state=domain.StoryState.DRAFTED),))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == "jtbd-1"
        assert str(jtbd.role) == "a developer"
        assert str(jtbd.i_want) == "my steps fixed in advance"
        assert str(jtbd.so_that) == "I can pick up where we were"
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a job to be done", "I submit it", "I can come back to it", "drafted",)]

    def test_a_jtbd_answers_record_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a job to be done", when="I submit it", then="I can come back to it"),)))

        assert isinstance(record_stories_outcome, domain.RecordStoriesOutcome)

    def test_a_jtbd_reads_its_status_as_one_of_its_values(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=()))

        assert str(jtbd.status) in [jtbd_status.value for jtbd_status in domain.JtbdStatus]

    def test_a_jtbd_without_stories_is_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_a_jtbd_with_a_drafted_story_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=(domain.StorySpec(given="a job to be done", when="I submit it", then="I can come back to it", state=domain.StoryState.DRAFTED),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recording_stories_keeps_each_story_text_as_a_drafted_story(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a job to be done", when="I submit it", then="I can come back to it"), domain.StoryTextSpec(given="a submitted job to be done", when="I read it", then="its stories are there"))))

        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a job to be done", "I submit it", "I can come back to it", "drafted"), ("a submitted job to be done", "I read it", "its stories are there", "drafted")]

    def test_recording_stories_leaves_the_jtbd_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a job to be done", when="I submit it", then="I can come back to it"),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recording_no_story_texts_is_refused(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=()))

        with pytest.raises(errors.DomainError):
            jtbd.record_stories(domain.RecordStoriesSpec(story_texts=()))

    def test_a_story_with_a_blank_given_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=(domain.StorySpec(given=" ", when="I submit it", then="I can come back to it", state=domain.StoryState.DRAFTED),)))
