# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="the steps fixed in advance", so_that="I can pick up where we left off", stories=(domain.StorySpec(given="a job to be done", when="I submit it", then="it is drafting its stories", state=domain.StoryState.DRAFTED),))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == "jtbd-1"
        assert str(jtbd.role) == "a developer"
        assert str(jtbd.i_want) == "the steps fixed in advance"
        assert str(jtbd.so_that) == "I can pick up where we left off"
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a job to be done", "I submit it", "it is drafting its stories", "drafted",)]

    def test_a_jtbd_answers_record_stories_with_one_of_its_outcomes(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="the steps fixed in advance", so_that="I can pick up where we left off", stories=()))

        record_stories_outcome = jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a job to be done", when="I submit it", then="it is drafting its stories"),)))

        assert isinstance(record_stories_outcome, domain.RecordStoriesOutcome)

    def test_a_jtbd_reads_its_status_as_one_of_its_values(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="the steps fixed in advance", so_that="I can pick up where we left off", stories=()))

        assert str(jtbd.status) in [jtbd_status.value for jtbd_status in domain.JtbdStatus]

    def test_a_jtbd_with_recorded_stories_awaits_story_acceptance_with_them_drafted(self) -> None:
        jtbd = domain.Jtbd(domain.JtbdSpec(jtbd_id="jtbd-1", role="a developer", i_want="the steps fixed in advance", so_that="I can pick up where we left off", stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(domain.StoryTextSpec(given="a job to be done", when="I submit it", then="it is drafting its stories"),)))

        assert str(jtbd.status) == "awaiting_story_acceptance"
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a job to be done", "I submit it", "it is drafting its stories", "drafted",)]
