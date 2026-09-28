from __future__ import annotations

import pytest

import drafting.domain as domain
import tesser.errors as errors


class TestRun:

    def test_a_run_constructs_from_its_spec(self) -> None:
        run_spec = domain.RunSpec(run_id="run-1", job="plan a migration")

        run = domain.Run(run_spec)

        assert str(run.identity) == run_spec.run_id
        assert str(run.job) == run_spec.job

    def test_a_new_run_is_at_the_drafting_stage_with_no_stories(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="run-1", job="plan a migration"))

        assert run.stage == domain.Stage(domain.RunStage.DRAFTING)
        assert run.stories == ()
        assert run.accepted_stories == ()

    def test_a_drafted_run_awaits_the_pick_with_the_drafted_stories_and_none_accepted(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="run-1", job="plan a migration"))
        draft = domain.Draft(domain.DraftSpec(stories=("As a developer, I want a plan",)))

        run.draft(draft)

        assert run.stage == domain.Stage(domain.RunStage.AWAITING_PICK)
        assert run.stories == draft.stories
        assert run.accepted_stories == ()

    def test_a_run_past_drafting_refuses_a_second_draft_and_keeps_the_first(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="run-1", job="plan a migration"))
        draft = domain.Draft(domain.DraftSpec(stories=("As a developer, I want a plan",)))
        run.draft(draft)

        with pytest.raises(errors.DomainError):
            run.draft(domain.Draft(domain.DraftSpec(stories=("As a developer, I want another plan",))))

        assert run.stories == draft.stories

    def test_two_runs_do_not_compare(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="run-1", job="plan a migration"))

        with pytest.raises(TypeError):
            hash(run)


class TestDraft:

    def test_a_draft_constructs_from_its_spec(self) -> None:
        draft_spec = domain.DraftSpec(stories=("As a developer, I want a plan", "As a developer, I want a review"))

        draft = domain.Draft(draft_spec)

        assert tuple(str(story) for story in draft.stories) == draft_spec.stories

    def test_a_draft_equals_by_value(self) -> None:
        first = domain.Draft(domain.DraftSpec(stories=("As a developer, I want a plan",)))
        second = domain.Draft(domain.DraftSpec(stories=("As a developer, I want a plan",)))

        assert first == second
        assert first != domain.Draft(domain.DraftSpec(stories=("As a developer, I want a review",)))

    def test_a_draft_with_no_stories_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Draft(domain.DraftSpec(stories=()))

    def test_a_draft_with_a_blank_story_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Draft(domain.DraftSpec(stories=("As a developer, I want a plan", "  ")))


class TestRunId:

    def test_a_run_id_equals_by_value(self) -> None:
        first = domain.RunId("run-1")
        second = domain.RunId("run-1")

        assert first == second
        assert first != domain.RunId("run-2")


class TestStage:

    def test_a_stage_equals_by_value(self) -> None:
        first = domain.Stage(domain.RunStage.DRAFTING)
        second = domain.Stage(domain.RunStage.DRAFTING)

        assert first == second
        assert first != domain.Stage(domain.RunStage.AWAITING_PICK)

    def test_a_stage_reads_as_its_state(self) -> None:
        assert str(domain.Stage(domain.RunStage.AWAITING_PICK)) == "awaiting_pick"
