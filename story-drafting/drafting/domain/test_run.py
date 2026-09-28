from __future__ import annotations

import pytest

import tesser.testing as ts

import drafting.domain as domain
import tesser.errors as errors


@ts.helper
def run_spec(
    run_id: str = "r1",
    job: str = "ship a release",
    step: str = "drafting",
    drafted_stories: tuple[str, ...] = (),
    accepted_stories: tuple[str, ...] = (),
) -> domain.RunSpec:
    return domain.RunSpec(
        run_id=run_id,
        job=job,
        step=step,
        drafted_stories=drafted_stories,
        accepted_stories=accepted_stories,
    )


class TestRun:

    def test_a_run_constructs_from_its_spec(self) -> None:
        run = domain.Run(run_spec(drafted_stories=("a story",), accepted_stories=("a story",)))

        assert run.identity == domain.RunId("r1")
        assert run.job == domain.Job("ship a release")
        assert run.step == domain.Step(domain.DRAFTING)
        assert run.drafted_stories == (domain.Story("a story"),)
        assert run.accepted_stories == (domain.Story("a story"),)

    def test_a_run_is_identified_by_its_id(self) -> None:
        assert domain.Run(run_spec(run_id="r1")) == domain.Run(run_spec(run_id="r1", job="another job"))
        assert domain.Run(run_spec(run_id="r1")) != domain.Run(run_spec(run_id="r2"))

    def test_a_run_refuses_a_story_that_says_nothing(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Run(run_spec(drafted_stories=("  ",)))


class TestRunId:

    def test_a_run_id_equality(self) -> None:
        assert domain.RunId("r1") == domain.RunId("r1")
        assert hash(domain.RunId("r1")) == hash(domain.RunId("r1"))
        assert domain.RunId("r1") != domain.RunId("r2")

    def test_a_run_id_is_never_empty(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.RunId("")

    def test_a_run_id_round_trips_through_its_string(self) -> None:
        assert domain.RunId(str(domain.RunId("r1"))) == domain.RunId("r1")


class TestJob:

    def test_a_job_equality(self) -> None:
        assert domain.Job(" ship a release ") == domain.Job("ship a release")
        assert hash(domain.Job(" ship a release ")) == hash(domain.Job("ship a release"))

    def test_a_job_says_something(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Job("   ")

    def test_a_job_round_trips_through_its_string(self) -> None:
        assert domain.Job(str(domain.Job("ship a release"))) == domain.Job("ship a release")


class TestStory:

    def test_a_story_equality(self) -> None:
        assert domain.Story(" a story ") == domain.Story("a story")
        assert hash(domain.Story(" a story ")) == hash(domain.Story("a story"))

    def test_a_story_says_something(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Story("")

    def test_a_story_round_trips_through_its_string(self) -> None:
        assert domain.Story(str(domain.Story("a story"))) == domain.Story("a story")


class TestStep:

    def test_a_step_equality(self) -> None:
        assert domain.Step("drafting") == domain.Step("drafting")
        assert hash(domain.Step("drafting")) == hash(domain.Step("drafting"))

    def test_a_step_outside_the_set_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Step("finished")

    def test_a_step_round_trips_through_its_string(self) -> None:
        assert domain.Step(str(domain.Step("drafting"))) == domain.Step("drafting")


class TestRunPresence:

    def test_presence_decides_the_lookup(self) -> None:
        assert domain.RunPresence(domain.RunPresenceSpec(presence="found")).decide() is domain.RunLookup.FOUND
        assert domain.RunPresence(domain.RunPresenceSpec(presence="not_found")).decide() is domain.RunLookup.NOT_FOUND

    def test_a_presence_outside_the_set_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.RunPresence(domain.RunPresenceSpec(presence="maybe"))


class TestDraftedStories:

    def test_drafted_stories_equality(self) -> None:
        assert domain.DraftedStories(domain.DraftedStoriesSpec(stories=(" a story ",))) == domain.DraftedStories(
            domain.DraftedStoriesSpec(stories=("a story",))
        )
        assert domain.DraftedStories(domain.DraftedStoriesSpec(stories=("a story",))) != domain.DraftedStories(
            domain.DraftedStoriesSpec(stories=("a story", "another story"))
        )

    def test_drafted_stories_carry_their_stories_in_order(self) -> None:
        drafted_stories = domain.DraftedStories(domain.DraftedStoriesSpec(stories=("first", "second")))

        assert drafted_stories.stories == (domain.Story("first"), domain.Story("second"))

    def test_a_draft_offers_at_least_one_story(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.DraftedStories(domain.DraftedStoriesSpec(stories=()))

    def test_a_draft_refuses_a_story_that_says_nothing(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.DraftedStories(domain.DraftedStoriesSpec(stories=("a story", " ")))


class TestStoriesDrafted:

    def test_a_drafting_run_given_its_stories_waits_for_the_pick_with_none_accepted(self) -> None:
        run = domain.Run(run_spec())

        run.stories_drafted(domain.DraftedStories(domain.DraftedStoriesSpec(stories=("first", "second"))))

        assert run.step == domain.Step(domain.AWAITING_PICK)
        assert run.drafted_stories == (domain.Story("first"), domain.Story("second"))
        assert run.accepted_stories == ()

    def test_a_run_past_drafting_refuses_a_second_draft_and_keeps_the_first(self) -> None:
        run = domain.Run(run_spec(step="awaiting_pick", drafted_stories=("first",)))

        with pytest.raises(errors.DomainError):
            run.stories_drafted(domain.DraftedStories(domain.DraftedStoriesSpec(stories=("second",))))

        assert run.step == domain.Step(domain.AWAITING_PICK)
        assert run.drafted_stories == (domain.Story("first"),)
