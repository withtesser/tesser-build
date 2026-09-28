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
        if value not in ("drafting", "awaiting_pick"):
            raise errors.invalid("invalid_stage", f"stage {value!r} is not a stage")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Story(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise errors.invalid("empty_story", "a drafted story is never empty")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


_DRAFTING: typing.Final[Stage] = Stage("drafting")
_AWAITING_PICK: typing.Final[Stage] = Stage("awaiting_pick")


class RunSpec(ts.Spec):

    def __init__(self, run_id: str, job: str) -> None:
        self.run_id = run_id
        self.job = job


class DraftedStoriesSpec(ts.Spec):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self.stories = stories


class DraftedStories(ts.ValueObject):

    _stories: tuple[Story, ...]

    def __init__(self, spec: DraftedStoriesSpec) -> None:
        stories = tuple(Story(story) for story in spec.stories)
        if not stories:
            raise errors.invalid("no_stories", "a draft offers at least one story to pick from")
        object.__setattr__(self, "_stories", stories)

    @property
    def stories(self) -> tuple[Story, ...]:
        return self._stories


class Run(ts.AggregateRoot):

    def __init__(self, spec: RunSpec) -> None:
        self._run_id = RunId(spec.run_id)
        self._job = Job(spec.job)
        self._stage = _DRAFTING
        self._stories: tuple[Story, ...] = ()

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
        return self._stories

    def offer_stories(self, drafted_stories: DraftedStories) -> None:
        if self._stage != _DRAFTING:
            raise errors.invalid("not_drafting", f"run {self._run_id!r} is not drafting")
        self._stories = drafted_stories.stories
        self._stage = _AWAITING_PICK
