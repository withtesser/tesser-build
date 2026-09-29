from __future__ import annotations

import tesser.domain as ts

import tesser.serialization as serialization


class JtbdId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Statement(ts.ValueObject):

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


class JobToBeDoneSpec(ts.Spec):

    def __init__(self, jtbd_id: str, statement: str, step: str, draft_count: int, picked_draft: str) -> None:
        self.jtbd_id = jtbd_id
        self.statement = statement
        self.step = step
        self.draft_count = draft_count
        self.picked_draft = picked_draft


class JobToBeDone(ts.AggregateRoot):

    def __init__(self, spec: JobToBeDoneSpec) -> None:
        self._jtbd_id = JtbdId(spec.jtbd_id)
        self._statement = Statement(spec.statement)
        self._step = Step(spec.step)
        self._draft_count = DraftCount(spec.draft_count)
        self._picked_draft = PickedDraft(spec.picked_draft)

    @property
    def identity(self) -> JtbdId:
        return self._jtbd_id

    @property
    def statement(self) -> Statement:
        return self._statement

    @property
    def step(self) -> Step:
        return self._step

    @property
    def draft_count(self) -> DraftCount:
        return self._draft_count

    @property
    def picked_draft(self) -> PickedDraft:
        return self._picked_draft
