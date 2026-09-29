from __future__ import annotations

import drafting.domain as domain


class TestRun:

    def test_a_run_constructs_from_its_spec(self) -> None:
        run_spec = domain.RunSpec(run_id="run-1", job="Plan a trip")

        run = domain.Run(run_spec)

        assert str(run.identity) == run_spec.run_id
        assert str(run.job) == run_spec.job


class TestRunId:

    def test_a_run_id_equals_by_value(self) -> None:
        first = domain.RunId("run-1")
        second = domain.RunId("run-1")

        assert first == second
        assert first != domain.RunId("run-2")
