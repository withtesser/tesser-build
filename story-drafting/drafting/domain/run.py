from __future__ import annotations

import enum

import tesser.domain as ts

import tesser.errors as errors
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


class Story(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise errors.invalid("empty_story", "a story says something")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class DraftSpec(ts.Spec):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self.stories = stories


class Draft(ts.ValueObject):

    _stories: tuple[Story, ...]

    def __init__(self, spec: DraftSpec) -> None:
        if not spec.stories:
            raise errors.invalid("empty_draft", "a draft holds at least one story")
        object.__setattr__(self, "_stories", tuple(Story(story) for story in spec.stories))

    @property
    def stories(self) -> tuple[Story, ...]:
        return tuple(self._stories)


class RunStage(enum.Enum):
    DRAFTING = "drafting"
    AWAITING_PICK = "awaiting_pick"


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
        self._stories: tuple[Story, ...] = ()
        self._accepted_stories: tuple[Story, ...] = ()

    @property
    def identity(self) -> RunId:
        return self._run_id

    @property
    def job(self) -> Job:
        return self._job

    @property
    def stage(self) -> Stage:
        return self._stage

    @property
    def stories(self) -> tuple[Story, ...]:
        return tuple(self._stories)

    @property
    def accepted_stories(self) -> tuple[Story, ...]:
        return tuple(self._accepted_stories)

    def draft(self, draft: Draft) -> None:
        if self._stage != Stage(RunStage.DRAFTING):
            raise errors.conflict("already_drafted", f"run {self._run_id} is past drafting")
        self._stories = draft.stories
        self._stage = Stage(RunStage.AWAITING_PICK)

    __eq__ = None  # type: ignore[assignment]
    __hash__ = None  # type: ignore[assignment]
