# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=(domain.StorySpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it", state=domain.StoryState.DRAFTED),))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == "jtbd-1"
        assert str(jtbd.role) == "a traveller"
        assert str(jtbd.i_want) == "one itinerary we all agreed on"
        assert str(jtbd.so_that) == "I can book it"
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a trip with three friends", "I propose an itinerary", "each friend can agree to it", "drafted",)]

    def test_a_jtbd_answers_record_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a trip with three friends", when="I propose an itinerary", then="each friend can agree to it"),)))

        assert isinstance(record_stories_outcome, domain.RecordStoriesOutcome)

    def test_a_jtbd_reads_its_status_as_one_of_its_values(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a traveller", i_want="one itinerary we all agreed on", so_that="I can book it", stories=()))

        assert str(jtbd.status) in [jtbd_status.value for jtbd_status in domain.JtbdStatus]
