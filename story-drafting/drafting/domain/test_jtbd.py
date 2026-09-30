# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import pytest

import tesser.errors as errors

import drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        story_spec = domain.StorySpec(given="a job to be done", when="I submit it", then="it is drafting its stories", state=domain.StoryState.DRAFTED)
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=(story_spec,))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == jtbd_spec.jtbd_id
        assert str(jtbd.role) == jtbd_spec.role
        assert str(jtbd.i_want) == jtbd_spec.i_want
        assert str(jtbd.so_that) == jtbd_spec.so_that
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_spec.given, story_spec.when, story_spec.then, story_spec.state.value,)]

    def test_a_jtbd_answers_record_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a job to be done", when="I submit it", then="it is drafting its stories"),)))

        assert isinstance(record_stories_outcome, domain.RecordStoriesOutcome)

    def test_a_jtbd_reads_its_status_as_one_of_its_values(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=()))

        assert str(jtbd.status) in [jtbd_status.value for jtbd_status in domain.JtbdStatus]

    def test_a_jtbd_with_no_stories_is_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_a_jtbd_whose_stories_are_recorded_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a job to be done", when="I submit it", then="it is drafting its stories"),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_a_jtbd_loaded_with_drafted_stories_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=(domain.StorySpec(given="a job to be done", when="I submit it", then="it is drafting its stories", state=domain.StoryState.DRAFTED),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recorded_stories_are_the_story_texts_each_drafted(self) -> None:
        story_text_spec = domain.StoryTextSpec(given="a job to be done", when="I submit it", then="it is drafting its stories")
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(story_text_spec,)))

        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_text_spec.given, story_text_spec.when, story_text_spec.then, domain.StoryState.DRAFTED.value,)]

    def test_recording_no_story_texts_is_refused(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=()))

        with pytest.raises(errors.DomainError):
            jtbd.record_stories(domain.RecordStoriesSpec(story_texts=()))

    def test_a_story_with_a_blank_given_is_refused(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", stories=()))

        with pytest.raises(errors.DomainError):
            jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given=" ", when="I submit it", then="it is drafting its stories"),)))
