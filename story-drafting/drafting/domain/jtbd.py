# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import enum

import tesser.domain as ts

import tesser.serialization as serialization


class JtbdStatus(enum.Enum):
    DRAFTING_STORIES = "drafting_stories"
    AWAITING_STORY_ACCEPTANCE = "awaiting_story_acceptance"


class StoryState(enum.Enum):
    DRAFTED = "drafted"
    ACCEPTED = "accepted"


class RecordStoriesOutcome(ts.Outcome):
    RECORDED = enum.auto()


class StoryViewSpec(ts.Spec):

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

    def __init__(self, jtbd_id: str, role: str, i_want: str, so_that: str, stories: tuple[StoryViewSpec, ...]) -> None:
        self.jtbd_id = jtbd_id
        self.role = role
        self.i_want = i_want
        self.so_that = so_that
        self.stories = stories


class Text(ts.ValueObject):

    _value: str

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class StoryView(ts.ValueObject):

    _given: Text
    _when: Text
    _then: Text
    _state: Text

    def __init__(self, spec: StoryViewSpec) -> None:
        object.__setattr__(self, "_given", Text(spec.given))
        object.__setattr__(self, "_when", Text(spec.when))
        object.__setattr__(self, "_then", Text(spec.then))
        object.__setattr__(self, "_state", Text(spec.state.value))

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
    def state(self) -> Text:
        return self._state


class DraftedStory(ts.ValueObject):

    _view: StoryView

    def __init__(self, spec: StoryTextSpec) -> None:
        object.__setattr__(
            self,
            "_view",
            StoryView(StoryViewSpec(given=spec.given, when=spec.when, then=spec.then, state=StoryState.DRAFTED)),
        )

    @property
    def view(self) -> StoryView:
        return self._view


class StoryDrafts(ts.ValueObject):

    _stories: tuple[StoryView, ...]

    def __init__(self, spec: RecordStoriesSpec) -> None:
        object.__setattr__(self, "_stories", tuple(DraftedStory(text).view for text in spec.story_texts))

    @property
    def stories(self) -> tuple[StoryView, ...]:
        return self._stories


class Jtbd(ts.AggregateRoot):

    def __init__(self, spec: JtbdSpec) -> None:
        self._jtbd_id = spec.jtbd_id
        self._role = spec.role
        self._i_want = spec.i_want
        self._so_that = spec.so_that
        self._stories = tuple(StoryView(story) for story in spec.stories)

    @property
    def identity(self) -> str:
        return self._jtbd_id

    def record_stories(self, record_stories_spec: RecordStoriesSpec) -> RecordStoriesOutcome:
        self._stories = StoryDrafts(record_stories_spec).stories
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
    def status(self) -> Text:
        if self._stories:
            return Text(JtbdStatus.AWAITING_STORY_ACCEPTANCE.value)
        return Text(JtbdStatus.DRAFTING_STORIES.value)

    @property
    def stories(self) -> tuple[StoryView, ...]:
        return self._stories
