from __future__ import annotations

import enum
import typing

import tesser.domain as ts

import tesser.errors as errors
import tesser.serialization as serialization

_DRAFTING: typing.Final[str] = "drafting"
_AWAITING_PICK: typing.Final[str] = "awaiting_pick"


class DraftingLookup(ts.Outcome):
    FOUND = enum.auto()
    NOT_FOUND = enum.auto()


class DraftingPresenceSpec(ts.Spec):

    def __init__(self, presence: str) -> None:
        self.presence = presence


class DraftingPresence(ts.ValueObject):

    _presence: str

    def __init__(self, spec: DraftingPresenceSpec) -> None:
        if spec.presence not in ("found", "not_found"):
            raise errors.invalid("invalid_presence", f"presence {spec.presence!r} is not a presence")
        object.__setattr__(self, "_presence", spec.presence)

    def decide(self) -> DraftingLookup:
        if self._presence == "found":
            return DraftingLookup.FOUND
        return DraftingLookup.NOT_FOUND


class DraftingId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value:
            raise errors.invalid("empty_drafting_id", "a drafting id is never empty")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Job(ts.ValueObject):

    _text: str

    def __init__(self, text: str) -> None:
        if not text.strip():
            raise errors.invalid("empty_job", "a job to be done says what the job is")
        object.__setattr__(self, "_text", text.strip())

    def __str__(self) -> str:
        return serialization.canonical_str(self._text)


class Step(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if value not in (_DRAFTING, _AWAITING_PICK):
            raise errors.invalid("invalid_step", f"step {value!r} is not a step of a drafting")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class StoryId(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value:
            raise errors.invalid("empty_story_id", "a story id is never empty")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class StoryText(ts.ValueObject):

    _text: str

    def __init__(self, text: str) -> None:
        if not text.strip():
            raise errors.invalid("empty_story", "a drafted story says something")
        object.__setattr__(self, "_text", text.strip())

    def __str__(self) -> str:
        return serialization.canonical_str(self._text)


class StorySpec(ts.Spec):

    def __init__(self, story_id: str, text: str) -> None:
        self.story_id = story_id
        self.text = text


class Story(ts.Entity):

    def __init__(self, spec: StorySpec) -> None:
        self._story_id = StoryId(spec.story_id)
        self._text = StoryText(spec.text)

    @property
    def identity(self) -> StoryId:
        return self._story_id

    @property
    def text(self) -> StoryText:
        return self._text


class DraftedStoriesSpec(ts.Spec):

    def __init__(self, texts: tuple[str, ...]) -> None:
        self.texts = texts


class DraftedStories(ts.ValueObject):

    _texts: tuple[StoryText, ...]

    def __init__(self, spec: DraftedStoriesSpec) -> None:
        if not spec.texts:
            raise errors.invalid("nothing_to_pick", "a drafting drafts at least one story to pick from")
        object.__setattr__(self, "_texts", tuple(StoryText(text) for text in spec.texts))

    @property
    def texts(self) -> tuple[StoryText, ...]:
        return self._texts


class DraftingSpec(ts.Spec):

    def __init__(
        self,
        drafting_id: str,
        job: str,
        step: str,
        stories: tuple[StorySpec, ...],
        accepted_stories: tuple[StorySpec, ...],
    ) -> None:
        self.drafting_id = drafting_id
        self.job = job
        self.step = step
        self.stories = stories
        self.accepted_stories = accepted_stories


_DRAFTING_STEP: typing.Final[Step] = Step(_DRAFTING)
_AWAITING_PICK_STEP: typing.Final[Step] = Step(_AWAITING_PICK)


class Drafting(ts.AggregateRoot):

    def __init__(self, spec: DraftingSpec) -> None:
        self._drafting_id = DraftingId(spec.drafting_id)
        self._job = Job(spec.job)
        self._step = Step(spec.step)
        self._stories = tuple(Story(story_spec) for story_spec in spec.stories)
        self._accepted_stories = tuple(Story(story_spec) for story_spec in spec.accepted_stories)
        if self._step == _DRAFTING_STEP and self._stories:
            raise errors.invalid("drafted_while_drafting", "a drafting still drafting has no stories yet")
        if self._step == _AWAITING_PICK_STEP and not self._stories:
            raise errors.invalid("nothing_to_pick", "a drafting awaiting the pick has stories to pick from")
        if not all(accepted_story in self._stories for accepted_story in self._accepted_stories):
            raise errors.invalid("foreign_accepted_story", "an accepted story is one of the drafted stories")

    @property
    def identity(self) -> DraftingId:
        return self._drafting_id

    @property
    def job(self) -> Job:
        return self._job

    @property
    def step(self) -> Step:
        return self._step

    @property
    def stories(self) -> tuple[Story, ...]:
        return self._stories

    @property
    def accepted_stories(self) -> tuple[Story, ...]:
        return self._accepted_stories

    def draft(self, drafted_stories: DraftedStories) -> None:
        if self._step != _DRAFTING_STEP:
            raise errors.invalid("already_drafted", "a drafting drafts its stories once")
        self._stories = tuple(
            Story(StorySpec(story_id=str(number), text=str(text)))
            for number, text in enumerate(drafted_stories.texts, start=1)
        )
        self._step = _AWAITING_PICK_STEP
