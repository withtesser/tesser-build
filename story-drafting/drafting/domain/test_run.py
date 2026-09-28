from __future__ import annotations

import pytest

import drafting.domain as domain
import tesser.errors as errors


class TestRunId:

    def test_run_id_equality(self) -> None:
        assert domain.RunId("r1") == domain.RunId("r1")
        assert domain.RunId("r1") != domain.RunId("r2")

    def test_an_empty_run_id_is_refused(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            domain.RunId("")
        assert excinfo.value.code == "empty_run_id"

    def test_a_dotted_run_id_is_refused(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            domain.RunId("..")
        assert excinfo.value.code == "dotted_run_id"


class TestStory:

    def test_story_equality(self) -> None:
        assert domain.Story(domain.StorySpec(text="a")) == domain.Story(domain.StorySpec(text="a"))
        assert domain.Story(domain.StorySpec(text="a")) != domain.Story(domain.StorySpec(text="b"))

    def test_a_blank_story_is_refused(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            domain.Story(domain.StorySpec(text="  "))
        assert excinfo.value.code == "empty_story"


class TestRun:

    def test_a_run_constructs_from_its_spec(self) -> None:
        run_spec = domain.RunSpec(
            run_id="r1",
            job="ship the release",
            stage="awaiting_pick",
            stories=(domain.StorySpec(text="As a developer, I want a release"),),
            accepted_stories=(),
        )
        run = domain.Run(run_spec)
        assert run.identity == domain.RunId(run_spec.run_id)
        assert str(run.job) == run_spec.job
        assert str(run.stage) == run_spec.stage
        assert run.stories == (domain.Story(domain.StorySpec(text="As a developer, I want a release")),)
        assert run.accepted_stories == ()

    def test_a_blank_job_refuses_the_run(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            domain.Run(domain.RunSpec(run_id="r1", job=" ", stage="drafting", stories=(), accepted_stories=()))
        assert excinfo.value.code == "empty_job"

    def test_a_stage_outside_the_set_refuses_the_run(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="done", stories=(), accepted_stories=()))
        assert excinfo.value.code == "invalid_stage"

    def test_a_blank_story_refuses_the_run(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(domain.StorySpec(text=""),), accepted_stories=()))
        assert excinfo.value.code == "empty_story"

    def test_a_blank_accepted_story_refuses_the_run(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=(domain.StorySpec(text=" "),)))
        assert excinfo.value.code == "empty_story"

    def test_the_stages_of_a_run_are_equal_by_value(self) -> None:
        drafting = domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=()))
        again = domain.Run(domain.RunSpec(run_id="r2", job="ship", stage="drafting", stories=(), accepted_stories=()))
        awaiting = domain.Run(domain.RunSpec(run_id="r3", job="ship", stage="awaiting_pick", stories=(), accepted_stories=()))
        assert drafting.stage == again.stage
        assert drafting.stage != awaiting.stage
        assert drafting.job == again.job
