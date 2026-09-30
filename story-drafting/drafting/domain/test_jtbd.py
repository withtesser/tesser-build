# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import pytest

import drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        story_spec = domain.StorySpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it", state=domain.StoryState.DRAFTED)
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=(story_spec,))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == jtbd_spec.jtbd_id
        assert str(jtbd.role) == jtbd_spec.role
        assert str(jtbd.i_want) == jtbd_spec.i_want
        assert str(jtbd.so_that) == jtbd_spec.so_that
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_spec.given, story_spec.when, story_spec.then, story_spec.state.value,)]

    def test_a_jtbd_answers_record_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it"),)))

        assert isinstance(record_stories_outcome, domain.RecordStoriesOutcome)

    def test_a_jtbd_reads_its_status_as_one_of_its_values(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        assert str(jtbd.status) in [jtbd_status.value for jtbd_status in domain.JtbdStatus]

    def test_a_jtbd_with_no_stories_is_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_recording_story_texts_keeps_each_as_a_drafted_story(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it"),)))

        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a trip with three friends", "I propose an itinerary", "each friend can agree to it", domain.StoryState.DRAFTED.value,)]

    def test_a_jtbd_whose_stories_are_recorded_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it"),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recording_no_story_texts_leaves_the_jtbd_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_recording_stories_a_second_time_keeps_the_first_stories(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=(domain.StorySpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it", state=domain.StoryState.DRAFTED),)))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a weekend alone", when="I plan a route", then="I can leave on friday"),)))

        assert [str(story.given) for story in jtbd.stories] == ["a trip with three friends"]

    def test_a_jtbd_whose_stories_are_all_decided_is_stories_decided(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=(domain.StorySpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it", state=domain.StoryState.ACCEPTED), domain.StorySpec(given="a weekend alone", when="I plan a route", then="I can leave on friday", state=domain.StoryState.REJECTED))))

        assert str(jtbd.status) == domain.JtbdStatus.STORIES_DECIDED.value

    def test_a_story_with_an_empty_given_is_refused(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        with pytest.raises(Exception):
            jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given=" ", when="I propose an itinerary", then="each friend can agree to it"),)))

    def test_two_stories_from_the_same_text_are_equal(self) -> None:
        first = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=(domain.StorySpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it", state=domain.StoryState.DRAFTED),)))
        second = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-2", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        second.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it"),)))

        assert first.stories == second.stories
