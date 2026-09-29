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


class Step(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class DraftCount(ts.ValueObject):

    _value: int

    def __init__(self, value: int) -> None:
        object.__setattr__(self, "_value", value)

    def __int__(self) -> int:
        return serialization.canonical_int(self._value)


class PickedDraft(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class JtbdSpec(ts.Spec):

    def __init__(self, jtbd_id: str, job: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.job = job
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class Jtbd(ts.AggregateRoot):

    def __init__(self, spec: JtbdSpec) -> None:
        self._jtbd_id = JtbdId(spec.jtbd_id)
        self._job = Job(spec.job)
        self._step = Step(spec.step)
        self._draft_count = DraftCount(spec.draft_count)
        self._picked_draft = PickedDraft(spec.picked_draft)

    @property
    def identity(self) -> JtbdId:
        return self._jtbd_id

    @property
    def job(self) -> Job:
        return self._job

    @property
    def step(self) -> Step:
        return self._step

    @property
    def draft_count(self) -> DraftCount:
        return self._draft_count

    @property
    def picked_draft(self) -> PickedDraft:
        return self._picked_draft
