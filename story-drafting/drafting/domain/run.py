from __future__ import annotations

import tesser.domain as ts

import tesser.errors as errors
import tesser.serialization as serialization


class RunId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value:
            raise errors.invalid("empty_run_id", "a run id is never empty")
        if value in (".", ".."):
            raise errors.invalid("dotted_run_id", "a run id is never '.' or '..'")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Job(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise errors.invalid("empty_job", "a job to be done is never blank")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Stage(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if value not in ("drafting", "awaiting_pick"):
            raise errors.invalid("invalid_stage", f"stage {value!r} is not a stage of a run")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class StorySpec(ts.Spec):

    def __init__(self, text: str) -> None:
        self.text = text


class Story(ts.ValueObject):

    _value: str

    def __init__(self, spec: StorySpec) -> None:
        if not spec.text.strip():
            raise errors.invalid("empty_story", "a user story is never blank")
        object.__setattr__(self, "_value", spec.text)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class RunSpec(ts.Spec):

    def __init__(
        self,
        run_id: str,
        job: str,
        stage: str,
        stories: tuple[StorySpec, ...],
        accepted_stories: tuple[StorySpec, ...],
    ) -> None:
        self.run_id = run_id
        self.job = job
        self.stage = stage
        self.stories = stories
        self.accepted_stories = accepted_stories


class Run(ts.AggregateRoot):

    def __init__(self, spec: RunSpec) -> None:
        self._id = RunId(spec.run_id)
        self._job = Job(spec.job)
        self._stage = Stage(spec.stage)
        self._stories = tuple(Story(story_spec) for story_spec in spec.stories)
        self._accepted_stories = tuple(Story(story_spec) for story_spec in spec.accepted_stories)

    @property
    def identity(self) -> RunId:
        return self._id

    @property
    def job(self) -> Job:
        return self._job

    @property
    def stage(self) -> Stage:
        return self._stage

    @property
    def stories(self) -> tuple[Story, ...]:
        return self._stories

    @property
    def accepted_stories(self) -> tuple[Story, ...]:
        return self._accepted_stories
