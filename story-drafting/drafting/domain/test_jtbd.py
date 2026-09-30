# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import pytest
import tesser.errors as errors
import tesser.testing as ts

import drafting.domain as domain


@ts.helper
def _story_spec(given: str = "a job to be done", when: str = "I submit it", then: str = "I can come back to it", state: domain.StoryState = domain.StoryState.DRAFTED) -> domain.StorySpec:
    return domain.StorySpec(given=given, when=when, then=then, state=state)


@ts.helper
def _story_text_spec(given: str = "a job to be done", when: str = "I submit it", then: str = "I can come back to it") -> domain.StoryTextSpec:
    return domain.StoryTextSpec(given=given, when=when, then=then)


@ts.helper
def _jtbd_spec(jtbd_id: str = "jtbd-1", role: str = "a developer", i_want: str = "my steps fixed in advance", so_that: str = "I can pick up where we were", stories: tuple[domain.StorySpec, ...] = ()) -> domain.JtbdSpec:
    return domain.JtbdSpec(jtbd_id=jtbd_id, role=role, i_want=i_want, so_that=so_that, stories=stories)


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        story_spec = _story_spec(given="a job to be done", when="I submit it", then="I can come back to it", state=domain.StoryState.DRAFTED)
        jtbd_spec = _jtbd_spec(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can pick up where we were", stories=(story_spec,))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == jtbd_spec.jtbd_id
        assert str(jtbd.role) == jtbd_spec.role
        assert str(jtbd.i_want) == jtbd_spec.i_want
        assert str(jtbd.so_that) == jtbd_spec.so_that
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_spec.given, story_spec.when, story_spec.then, story_spec.state.value,)]

    def test_a_jtbd_answers_record_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(),)))

        assert isinstance(record_stories_outcome, domain.RecordStoriesOutcome)

    def test_a_jtbd_reads_its_status_as_one_of_its_values(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        assert str(jtbd.status) in [jtbd_status.value for jtbd_status in domain.JtbdStatus]

    def test_a_jtbd_without_stories_is_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_a_jtbd_with_a_drafted_story_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=(_story_spec(state=domain.StoryState.DRAFTED),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recording_stories_keeps_each_story_text_as_a_drafted_story(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))
        first = _story_text_spec(given="a job to be done", when="I submit it", then="I can come back to it")
        second = _story_text_spec(given="drafted stories", when="I read the job to be done", then="I see its stories")

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(first, second)))

        assert [(str(story.given), str(story.when), str(story.then), str(story.state)) for story in jtbd.stories] == [
            (first.given, first.when, first.then, domain.StoryState.DRAFTED.value),
            (second.given, second.when, second.then, domain.StoryState.DRAFTED.value),
        ]

    def test_recording_stories_leaves_the_jtbd_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recording_no_story_texts_is_refused(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        with pytest.raises(errors.DomainError):
            jtbd.record_stories(domain.RecordStoriesSpec(story_texts=()))

    def test_a_story_with_a_blank_then_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Jtbd(_jtbd_spec(stories=(_story_spec(then=" "),)))

    def test_stories_with_the_same_text_and_state_are_equal(self) -> None:
        story_spec = _story_spec()

        left = domain.Jtbd(_jtbd_spec(stories=(story_spec,))).stories
        right = domain.Jtbd(_jtbd_spec(stories=(story_spec,))).stories

        assert left == right and hash(left) == hash(right)

    def test_stories_with_different_text_are_not_equal(self) -> None:
        left = domain.Jtbd(_jtbd_spec(stories=(_story_spec(then="I can come back to it"),))).stories

        right = domain.Jtbd(_jtbd_spec(stories=(_story_spec(then="I see it drafting"),))).stories

        assert left != right
