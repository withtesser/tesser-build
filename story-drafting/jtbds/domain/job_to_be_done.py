from __future__ import annotations

import tesser.domain as ts

import tesser.serialization as serialization


class JtbdId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Description(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Status(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class JobToBeDoneSpec(ts.Spec):

    def __init__(self, jtbd_id: str, description: str, status: str) -> None:
        self.jtbd_id = jtbd_id
        self.description = description
        self.status = status


class JobToBeDone(ts.AggregateRoot):

    def __init__(self, spec: JobToBeDoneSpec) -> None:
        self._jtbd_id = JtbdId(spec.jtbd_id)
        self._description = Description(spec.description)
        self._status = Status(spec.status)

    @property
    def identity(self) -> JtbdId:
        return self._jtbd_id

    @property
    def description(self) -> Description:
        return self._description

    @property
    def status(self) -> Status:
        return self._status
