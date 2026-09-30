# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import pytest

import tesser.errors as errors
import tesser.testing as ts

import drafting.domain as domain


@ts.helper
def _story_spec(given: str = "a trip with three friends", when: str = "I propose an itinerary", then: str = "each friend can agree to it", state: domain.StoryState = domain.StoryState.DRAFTED) -> domain.StorySpec:
    return domain.StorySpec(given=given, when=when, then=then, state=state)


@ts.helper
def _jtbd_spec(jtbd_id: str = "jtbd-1", role: str = "a traveller", i_want: str = "one itinerary we all agreed on", so_that: str = "I can book it", stories: tuple[domain.StorySpec, ...] = ()) -> domain.JtbdSpec:
    return domain.JtbdSpec(jtbd_id=jtbd_id, role=role, i_want=i_want, so_that=so_that, stories=stories)


@ts.helper
def _story_text_spec(given: str = "a trip with three friends", when: str = "I propose an itinerary", then: str = "each friend can agree to it") -> domain.StoryTextSpec:
    return domain.StoryTextSpec(given=given, when=when, then=then)


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        story_spec = _story_spec()
        jtbd_spec = _jtbd_spec(stories=(story_spec,))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == jtbd_spec.jtbd_id
        assert str(jtbd.role) == jtbd_spec.role
        assert str(jtbd.i_want) == jtbd_spec.i_want
        assert str(jtbd.so_that) == jtbd_spec.so_that
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_spec.given, story_spec.when, story_spec.then, story_spec.state.value,)]

    def test_a_jtbd_refuses_a_story_with_an_empty_given(self) -> None:
        jtbd_spec = _jtbd_spec(stories=(_story_spec(given=""),))

        with pytest.raises(errors.DomainError):
            domain.Jtbd(jtbd_spec)

    def test_a_jtbd_answers_record_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(),)))

        assert isinstance(record_stories_outcome, domain.RecordStoriesOutcome)

    def test_a_jtbd_with_no_stories_is_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_recording_story_texts_keeps_each_as_a_drafted_story(self) -> None:
        story_text_spec = _story_text_spec()
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(story_text_spec,)))

        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_text_spec.given, story_text_spec.when, story_text_spec.then, domain.StoryState.DRAFTED.value,)]

    def test_a_jtbd_whose_stories_are_recorded_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_a_jtbd_whose_stories_are_all_decided_is_stories_decided(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=(_story_spec(state=domain.StoryState.ACCEPTED), _story_spec(state=domain.StoryState.REJECTED))))

        assert str(jtbd.status) == domain.JtbdStatus.STORIES_DECIDED.value

    def test_recording_no_story_texts_leaves_the_jtbd_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_recording_again_keeps_the_stories_first_recorded(self) -> None:
        story_spec = _story_spec(given="the first given")
        jtbd = domain.Jtbd(_jtbd_spec(stories=(story_spec,)))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(given="another given"),)))

        assert [str(story.given) for story in jtbd.stories] == [story_spec.given]

    def test_recording_a_story_text_with_an_empty_then_is_refused(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        with pytest.raises(errors.DomainError):
            jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(then=""),)))
