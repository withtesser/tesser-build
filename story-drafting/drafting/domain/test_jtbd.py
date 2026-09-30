# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import typing

import pytest

import tesser.errors as errors
import tesser.testing as ts

import drafting.domain as domain


@ts.helper
def _story_text_spec(given: str = "a trip with three friends", when: str = "I propose an itinerary", then: str = "each friend can agree to it") -> domain.StoryTextSpec:
    return domain.StoryTextSpec(given=given, when=when, then=then)


@ts.helper
def _story_spec(given: str = "a trip with three friends", when: str = "I propose an itinerary", then: str = "each friend can agree to it", state: domain.StoryState = domain.StoryState.DRAFTED) -> domain.StorySpec:
    return domain.StorySpec(given=given, when=when, then=then, state=state)


@ts.helper
def _jtbd_spec(jtbd_id: str = "jtbd-1", role: str = "a traveller", i_want: str = "one itinerary we all agreed on", so_that: str = "I can book it", stories: tuple[domain.StorySpec, ...] = ()) -> domain.JtbdSpec:
    return domain.JtbdSpec(jtbd_id=jtbd_id, role=role, i_want=i_want, so_that=so_that, stories=stories)


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=(domain.StorySpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it", state=domain.StoryState.DRAFTED),))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == jtbd_spec.jtbd_id
        assert str(jtbd.role) == jtbd_spec.role
        assert str(jtbd.i_want) == jtbd_spec.i_want
        assert str(jtbd.so_that) == jtbd_spec.so_that
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story.given, story.when, story.then, story.state.value,) for story in jtbd_spec.stories]

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
        jtbd = domain.Jtbd(_jtbd_spec(stories=(_story_spec(state=domain.StoryState.ACCEPTED), _story_spec(state=domain.StoryState.DRAFTED))))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_a_jtbd_whose_stories_are_none_drafted_has_its_stories_decided(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=(_story_spec(state=domain.StoryState.ACCEPTED), _story_spec(state=domain.StoryState.REJECTED))))

        assert str(jtbd.status) == domain.JtbdStatus.STORIES_DECIDED.value

    def test_recording_story_texts_keeps_each_as_a_drafted_story(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))
        story_text_spec = _story_text_spec(given="a trip", when="I propose", then="they agree")

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(story_text_spec,)))

        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_text_spec.given, story_text_spec.when, story_text_spec.then, domain.StoryState.DRAFTED.value,)]

    def test_recording_story_texts_answers_recorded(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(),)))

        match record_stories_outcome:
            case domain.RecordStoriesOutcome.RECORDED:
                pass
            case domain.RecordStoriesOutcome.ALREADY_RECORDED | domain.RecordStoriesOutcome.NONE_GIVEN:
                pytest.fail("story texts given to a jtbd without stories are recorded")
            case _ as never:
                typing.assert_never(never)

    def test_recording_story_texts_makes_a_jtbd_await_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recording_no_story_texts_answers_none_given_and_keeps_no_stories(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=()))

        match record_stories_outcome:
            case domain.RecordStoriesOutcome.NONE_GIVEN:
                assert jtbd.stories == ()
            case domain.RecordStoriesOutcome.RECORDED | domain.RecordStoriesOutcome.ALREADY_RECORDED:
                pytest.fail("a story drafting that yields none is not recorded")
            case _ as never:
                typing.assert_never(never)

    def test_recording_stories_again_answers_already_recorded_and_keeps_the_first(self) -> None:
        story_spec = _story_spec(given="the first story")
        jtbd = domain.Jtbd(_jtbd_spec(stories=(story_spec,)))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(given="a second story"),)))

        match record_stories_outcome:
            case domain.RecordStoriesOutcome.ALREADY_RECORDED:
                assert [str(story.given) for story in jtbd.stories] == [story_spec.given]
            case domain.RecordStoriesOutcome.RECORDED | domain.RecordStoriesOutcome.NONE_GIVEN:
                pytest.fail("recording stories is done once")
            case _ as never:
                typing.assert_never(never)

    def test_a_story_with_empty_text_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Jtbd(_jtbd_spec(stories=(_story_spec(then=""),)))

    def test_a_story_text_with_empty_text_is_refused(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        with pytest.raises(errors.DomainError):
            jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(when=" "),)))
