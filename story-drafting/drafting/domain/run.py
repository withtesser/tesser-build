from __future__ import annotations

import enum

import tesser.domain as ts

import tesser.serialization as serialization


class RunId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Job(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class RunStage(enum.Enum):
    DRAFTING = "drafting"


class Stage(ts.ValueObject):

    def __init__(self, value: RunStage) -> None:
        object.__setattr__(self, "_value", value.value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)

    _value: str


class RunSpec(ts.Spec):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class Run(ts.AggregateRoot):

    def __init__(self, spec: RunSpec) -> None:
        self._run_id = RunId(spec.run_id)
        self._job = Job(spec.job)
        self._stage = Stage(RunStage.DRAFTING)

    @property
    def identity(self) -> RunId:
        return self._run_id

    @property
    def job(self) -> Job:
        return self._job

    @property
    def stage(self) -> Stage:
        return self._stage
