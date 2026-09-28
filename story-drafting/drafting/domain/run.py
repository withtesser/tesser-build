from __future__ import annotations

import typing

import tesser.domain as ts

import tesser.errors as errors
import tesser.serialization as serialization


class RunId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value:
            raise errors.invalid("empty_run_id", "a run id is never empty")
        if value in (".", ".."):
            raise errors.invalid("dot_run_id", f"a run id is never {value!r}")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Job(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise errors.invalid("empty_job", "a job to be done is never empty")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Stage(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if value not in ("drafting",):
            raise errors.invalid("invalid_stage", f"stage {value!r} is not a stage")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


_DRAFTING: typing.Final[Stage] = Stage("drafting")


class RunSpec(ts.Spec):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class Run(ts.AggregateRoot):

    def __init__(self, spec: RunSpec) -> None:
        self._run_id = RunId(spec.run_id)
        self._job = Job(spec.job)
        self._stage = _DRAFTING

    @property
    def identity(self) -> RunId:
        return self._run_id

    @property
    def job(self) -> Job:
        return self._job

    @property
    def stage(self) -> Stage:
        return self._stage
