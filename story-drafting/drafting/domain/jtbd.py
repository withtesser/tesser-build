from __future__ import annotations

import tesser.domain as ts

import tesser.serialization as serialization


class JtbdId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Situation(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Motivation(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Outcome(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class JtbdSpec(ts.Spec):

    def __init__(self, jtbd_id: str, situation: str, motivation: str, outcome: str) -> None:
        self.jtbd_id = jtbd_id
        self.situation = situation
        self.motivation = motivation
        self.outcome = outcome


class Jtbd(ts.AggregateRoot):

    def __init__(self, spec: JtbdSpec) -> None:
        self._jtbd_id = JtbdId(spec.jtbd_id)
        self._situation = Situation(spec.situation)
        self._motivation = Motivation(spec.motivation)
        self._outcome = Outcome(spec.outcome)

    @property
    def identity(self) -> JtbdId:
        return self._jtbd_id

    @property
    def situation(self) -> Situation:
        return self._situation

    @property
    def motivation(self) -> Motivation:
        return self._motivation

    @property
    def outcome(self) -> Outcome:
        return self._outcome
