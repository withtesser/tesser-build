from __future__ import annotations

import drafting.domain as domain


class TestRun:

    def test_a_run_constructs_from_its_spec(self) -> None:
        run_spec = domain.RunSpec(run_id="run-1", job="plan a migration")

        run = domain.Run(run_spec)

        assert str(run.identity) == run_spec.run_id
        assert str(run.job) == run_spec.job

    def test_a_new_run_is_at_the_drafting_stage(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="run-1", job="plan a migration"))

        assert run.stage == domain.Stage(domain.RunStage.DRAFTING)


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

    def test_a_stage_reads_as_its_state(self) -> None:
        assert str(domain.Stage(domain.RunStage.DRAFTING)) == "drafting"
