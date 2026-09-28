from __future__ import annotations

import enum
import typing

import tesser.domain as ts

import tesser.errors as errors
import tesser.serialization as serialization

DRAFTING: typing.Final[str] = "drafting"
AWAITING_PICK: typing.Final[str] = "awaiting_pick"
_STEPS: typing.Final[tuple[str, ...]] = (DRAFTING, AWAITING_PICK)


class RunId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value:
            raise errors.invalid("empty_run_id", "a run id is never empty")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Job(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise errors.invalid("empty_job", "a job to be done says something")
        object.__setattr__(self, "_value", value.strip())

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Story(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise errors.invalid("empty_story", "a story says something")
        object.__setattr__(self, "_value", value.strip())

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Step(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if value not in _STEPS:
            raise errors.invalid("invalid_step", f"step {value!r} is not a step of a run")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class DraftedStoriesSpec(ts.Spec):

    def __init__(self, stories: tuple[str, ...]) -> None:
        self.stories = stories


class DraftedStories(ts.ValueObject):

    _stories: tuple[Story, ...]

    def __init__(self, spec: DraftedStoriesSpec) -> None:
        stories = tuple(Story(story) for story in spec.stories)
        if not stories:
            raise errors.invalid("no_drafted_stories", "a draft offers at least one story to pick from")
        object.__setattr__(self, "_stories", stories)

    @property
    def stories(self) -> tuple[Story, ...]:
        return self._stories


class RunLookup(ts.Outcome):
    FOUND = enum.auto()
    NOT_FOUND = enum.auto()


class RunPresenceSpec(ts.Spec):

    def __init__(self, presence: str) -> None:
        self.presence = presence


class RunPresence(ts.ValueObject):

    _presence: str

    def __init__(self, spec: RunPresenceSpec) -> None:
        if spec.presence not in ("found", "not_found"):
            raise errors.invalid("invalid_presence", f"presence {spec.presence!r} is not a presence")
        object.__setattr__(self, "_presence", spec.presence)

    def decide(self) -> RunLookup:
        if self._presence == "found":
            return RunLookup.FOUND
        return RunLookup.NOT_FOUND


class RunSpec(ts.Spec):

    def __init__(
        self,
        run_id: str,
        job: str,
        step: str,
        drafted_stories: tuple[str, ...],
        accepted_stories: tuple[str, ...],
    ) -> None:
        self.run_id = run_id
        self.job = job
        self.step = step
        self.drafted_stories = drafted_stories
        self.accepted_stories = accepted_stories


class Run(ts.AggregateRoot):

    def __init__(self, spec: RunSpec) -> None:
        self._run_id = RunId(spec.run_id)
        self._job = Job(spec.job)
        self._step = Step(spec.step)
        self._drafted_stories = tuple(Story(story) for story in spec.drafted_stories)
        self._accepted_stories = tuple(Story(story) for story in spec.accepted_stories)

    @property
    def identity(self) -> RunId:
        return self._run_id

    @property
    def job(self) -> Job:
        return self._job

    @property
    def step(self) -> Step:
        return self._step

    @property
    def drafted_stories(self) -> tuple[Story, ...]:
        return self._drafted_stories

    @property
    def accepted_stories(self) -> tuple[Story, ...]:
        return self._accepted_stories

    def stories_drafted(self, drafted_stories: DraftedStories) -> None:
        if self._step != Step(DRAFTING):
            raise errors.invalid("not_drafting", f"run {self._run_id} is past drafting")
        self._drafted_stories = drafted_stories.stories
        self._step = Step(AWAITING_PICK)
