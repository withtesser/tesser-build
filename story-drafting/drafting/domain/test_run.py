from __future__ import annotations

import pytest

import drafting.domain as domain
import tesser.errors as errors


class TestRun:

    def test_a_run_constructs_from_its_spec_and_starts_drafting(self) -> None:
        run_spec = domain.RunSpec(run_id="r1", job="ship a release without re-explaining the steps")
        run = domain.Run(run_spec)
        assert str(run.identity) == run_spec.run_id
        assert str(run.job) == run_spec.job
        assert str(run.stage) == "drafting"

    def test_an_empty_run_id_refuses_the_run(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Run(domain.RunSpec(run_id="", job="a job"))

    def test_a_dot_run_id_refuses_the_run(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Run(domain.RunSpec(run_id="..", job="a job"))

    def test_a_blank_job_refuses_the_run(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Run(domain.RunSpec(run_id="r1", job="  "))


class TestRunId:

    def test_a_run_id_equals_by_value(self) -> None:
        first = domain.RunId("r1")
        second = domain.RunId("r1")
        assert first == second
        assert first != domain.RunId("r2")

    def test_string_is_the_canonical_exit(self) -> None:
        assert str(domain.RunId("r1")) == "r1"


class TestJob:

    def test_a_job_equals_by_value(self) -> None:
        first = domain.Job("a job")
        second = domain.Job("a job")
        assert first == second
        assert first != domain.Job("another job")

    def test_string_is_the_canonical_exit(self) -> None:
        assert str(domain.Job("a job")) == "a job"


class TestOfferingStories:

    def test_a_drafting_run_offered_stories_awaits_the_pick_with_them(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="r1", job="a job"))
        run.offer_stories(domain.DraftedStories(domain.DraftedStoriesSpec(stories=("first story", "second story"))))
        assert str(run.stage) == "awaiting_pick"
        assert run.stories == (domain.Story("first story"), domain.Story("second story"))

    def test_a_run_starts_with_no_stories(self) -> None:
        assert domain.Run(domain.RunSpec(run_id="r1", job="a job")).stories == ()


    def test_a_run_already_awaiting_the_pick_is_not_offered_stories_again(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="r1", job="a job"))
        run.offer_stories(domain.DraftedStories(domain.DraftedStoriesSpec(stories=("a story",))))
        with pytest.raises(errors.DomainError) as refused:
            run.offer_stories(domain.DraftedStories(domain.DraftedStoriesSpec(stories=("another story",))))
        assert refused.value.code == "not_drafting"
        assert run.stories == (domain.Story("a story"),)


class TestDraftedStories:

    def test_drafted_stories_hold_each_story_in_order(self) -> None:
        drafted_stories_spec = domain.DraftedStoriesSpec(stories=("first story", "second story"))
        drafted_stories = domain.DraftedStories(drafted_stories_spec)
        assert drafted_stories.stories == (domain.Story("first story"), domain.Story("second story"))

    def test_no_stories_to_pick_from_is_refused(self) -> None:
        with pytest.raises(errors.DomainError) as refused:
            domain.DraftedStories(domain.DraftedStoriesSpec(stories=()))
        assert refused.value.code == "no_stories"

    def test_a_blank_story_is_refused(self) -> None:
        with pytest.raises(errors.DomainError) as refused:
            domain.DraftedStories(domain.DraftedStoriesSpec(stories=("a story", " ")))
        assert refused.value.code == "empty_story"

    def test_drafted_stories_equal_by_value(self) -> None:
        first = domain.DraftedStories(domain.DraftedStoriesSpec(stories=("a story",)))
        second = domain.DraftedStories(domain.DraftedStoriesSpec(stories=("a story",)))
        assert first == second
        assert first != domain.DraftedStories(domain.DraftedStoriesSpec(stories=("another story",)))


class TestStory:

    def test_a_story_equals_by_value(self) -> None:
        first = domain.Story("a story")
        second = domain.Story("a story")
        assert first == second
        assert first != domain.Story("another story")

    def test_string_is_the_canonical_exit(self) -> None:
        assert str(domain.Story("a story")) == "a story"
