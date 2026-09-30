# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import enum

import tesser.domain as ts

import tesser.errors as errors
import tesser.serialization as serialization


class StoryState(enum.Enum):
    DRAFTED = "drafted"


class JtbdStatus(enum.Enum):
    DRAFTING_STORIES = "drafting_stories"
    AWAITING_STORY_ACCEPTANCE = "awaiting_story_acceptance"


class RecordStoriesOutcome(ts.Outcome):
    RECORDED = enum.auto()


class StorySpec(ts.Spec):

    def __init__(self, given: str, when: str, then: str, state: StoryState) -> None:
        self.given = given
        self.when = when
        self.then = then
        self.state = state


class StoryTextSpec(ts.Spec):

    def __init__(self, given: str, when: str, then: str) -> None:
        self.given = given
        self.when = when
        self.then = then


class RecordStoriesSpec(ts.Spec):

    def __init__(self, story_texts: tuple[StoryTextSpec, ...]) -> None:
        self.story_texts = story_texts


class JtbdSpec(ts.Spec):

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str, stories: tuple[StorySpec, ...]) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that
        self.stories = stories


class Text(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        if not value.strip():
            raise errors.invalid("invalid_text", "a story's given, when, and then must not be blank")
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class StoryStateValue(ts.ValueObject):

    _value: str

    def __init__(self, value: StoryState) -> None:
        object.__setattr__(self, "_value", value.value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class JtbdStatusValue(ts.ValueObject):

    _value: str

    def __init__(self, value: JtbdStatus) -> None:
        object.__setattr__(self, "_value", value.value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Story(ts.ValueObject):

    _given: Text
    _when: Text
    _then: Text
    _state: StoryStateValue

    def __init__(self, spec: StorySpec) -> None:
        object.__setattr__(self, "_given", Text(spec.given))
        object.__setattr__(self, "_when", Text(spec.when))
        object.__setattr__(self, "_then", Text(spec.then))
        object.__setattr__(self, "_state", StoryStateValue(spec.state))

    @property
    def given(self) -> Text:
        return self._given

    @property
    def when(self) -> Text:
        return self._when

    @property
    def then(self) -> Text:
        return self._then

    @property
    def state(self) -> StoryStateValue:
        return self._state


class StoryText(ts.ValueObject):

    _given: Text
    _when: Text
    _then: Text

    def __init__(self, spec: StoryTextSpec) -> None:
        object.__setattr__(self, "_given", Text(spec.given))
        object.__setattr__(self, "_when", Text(spec.when))
        object.__setattr__(self, "_then", Text(spec.then))

    def drafted(self) -> Story:
        return Story(StorySpec(given=str(self._given), when=str(self._when), then=str(self._then), state=StoryState.DRAFTED))


class StoryTexts(ts.ValueObject):

    _story_texts: tuple[StoryText, ...]

    def __init__(self, spec: RecordStoriesSpec) -> None:
        if not spec.story_texts:
            raise errors.invalid("no_story_texts", "a story drafting yields at least one story")
        object.__setattr__(self, "_story_texts", tuple(StoryText(story_text) for story_text in spec.story_texts))

    def drafted(self) -> tuple[Story, ...]:
        return tuple(story_text.drafted() for story_text in self._story_texts)


class Jtbd(ts.AggregateRoot):

    def __init__(self, spec: JtbdSpec) -> None:
        self._jtbd_id = spec.jtbd_id
        self._role = spec.role
        self._i_want = spec.i_want
        self._so_that = spec.so_that
        self._stories = tuple(Story(story) for story in spec.stories)

    @property
    def identity(self) -> str:
        return self._jtbd_id

    def record_stories(self, record_stories_spec: RecordStoriesSpec) -> RecordStoriesOutcome:
        self._stories = StoryTexts(record_stories_spec).drafted()
        return RecordStoriesOutcome.RECORDED

    @property
    def jtbd_id(self) -> str:
        return self._jtbd_id

    @property
    def role(self) -> str:
        return self._role

    @property
    def i_want(self) -> str:
        return self._i_want

    @property
    def so_that(self) -> str:
        return self._so_that

    @property
    def stories(self) -> tuple[Story, ...]:
        return self._stories

    @property
    def status(self) -> JtbdStatusValue:
        if any(story.state == StoryStateValue(StoryState.DRAFTED) for story in self._stories):
            return JtbdStatusValue(JtbdStatus.AWAITING_STORY_ACCEPTANCE)
        return JtbdStatusValue(JtbdStatus.DRAFTING_STORIES)
