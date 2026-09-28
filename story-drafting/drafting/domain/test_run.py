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
