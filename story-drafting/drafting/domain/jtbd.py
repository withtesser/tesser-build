from __future__ import annotations

import tesser.domain as ts

import tesser.serialization as serialization


class JtbdId(ts.ValueObject):

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


class JtbdSpec(ts.Spec):

    def __init__(self, jtbd_id: str, job: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job


class Jtbd(ts.AggregateRoot):

    def __init__(self, spec: JtbdSpec) -> None:
        self._jtbd_id = JtbdId(spec.jtbd_id)
        self._job = Job(spec.job)

    @property
    def identity(self) -> JtbdId:
        return self._jtbd_id

    @property
    def job(self) -> Job:
        return self._job
