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


class DraftStoriesOutcome(ts.Outcome):
    DRAFTED = enum.auto()


class StorySpec(ts.Spec):

    def __init__(self, given: str, when: str, then: str, state: StoryState) -> None:
        self.given = given
        self.when = when
        self.then = then
        self.state = state


class DraftStoriesSpec(ts.Spec):

    def __init__(self) -> None:
        pass


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
        object.__setattr__(self, "_value", value)

    def __str__(self) -> str:
        return serialization.canonical_str(self._value)


class Story(ts.ValueObject):

    _given: Text
    _when: Text
    _then: Text
    _state: Text

    def __init__(self, spec: StorySpec) -> None:
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

    def draft_stories(self, draft_stories_spec: DraftStoriesSpec) -> DraftStoriesOutcome:
        self._stories = (
            Story(
                StorySpec(
                    given=f"I am {self._role}",
                    when=f"I get {self._i_want}",
                    then=f"I can see that {self._so_that}",
                    state=StoryState.DRAFTED,
                )
            ),
        )
        return DraftStoriesOutcome.DRAFTED

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
    def stories(self) -> tuple[Story, ...]:
        return self._stories
