# pragma: tesser-agent-owned; generated once as a stub, the agent owns it from here
from __future__ import annotations

import tesser.testing as ts

import drafting.domain as domain


@ts.helper
def _story_spec(given: str = "a job to be done", when: str = "I submit it", then: str = "it is drafting", state: domain.StoryState = domain.StoryState.DRAFTED) -> domain.StorySpec:
    return domain.StorySpec(given=given, when=when, then=then, state=state)


@ts.helper
def _story_text_spec(given: str = "a job to be done", when: str = "I submit it", then: str = "it is drafting") -> domain.StoryTextSpec:
    return domain.StoryTextSpec(given=given, when=when, then=then)


@ts.helper
def _jtbd_spec(jtbd_id: str = "jtbd-1", role: str = "a developer", i_want: str = "stories drafted", so_that: str = "I can accept them", stories: tuple[domain.StorySpec, ...] = ()) -> domain.JtbdSpec:
    return domain.JtbdSpec(jtbd_id=jtbd_id, role=role, i_want=i_want, so_that=so_that, stories=stories)


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        story_spec = _story_spec()
        jtbd_spec = _jtbd_spec(stories=(story_spec,))

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.jtbd_id) == jtbd_spec.jtbd_id
        assert str(jtbd.role) == jtbd_spec.role
        assert str(jtbd.i_want) == jtbd_spec.i_want
        assert str(jtbd.so_that) == jtbd_spec.so_that
        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [(story_spec.given, story_spec.when, story_spec.then, story_spec.state.value,)]

    def test_a_jtbd_with_no_stories_is_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_a_jtbd_with_a_drafted_story_is_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=(_story_spec(state=domain.StoryState.ACCEPTED), _story_spec(state=domain.StoryState.DRAFTED))))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_a_jtbd_whose_stories_are_none_drafted_has_its_stories_decided(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=(_story_spec(state=domain.StoryState.ACCEPTED), _story_spec(state=domain.StoryState.REJECTED))))

        assert str(jtbd.status) == domain.JtbdStatus.STORIES_DECIDED.value

    def test_recording_story_texts_keeps_each_as_a_drafted_story(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))
        story_text_spec = _story_text_spec(given="a submitted job", when="I read it", then="I see its stories")

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(story_text_spec,)))

        assert [(str(story.given), str(story.when), str(story.then), str(story.state),) for story in jtbd.stories] == [("a submitted job", "I read it", "I see its stories", "drafted",)]

    def test_recording_story_texts_leaves_the_jtbd_awaiting_story_acceptance(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(),)))

        assert str(jtbd.status) == domain.JtbdStatus.AWAITING_STORY_ACCEPTANCE.value

    def test_recording_no_story_texts_leaves_the_jtbd_drafting_stories(self) -> None:
        jtbd = domain.Jtbd(_jtbd_spec(stories=()))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=()))

        assert str(jtbd.status) == domain.JtbdStatus.DRAFTING_STORIES.value

    def test_recording_again_keeps_the_stories_first_recorded(self) -> None:
        story_spec = _story_spec(given="the first story")
        jtbd = domain.Jtbd(_jtbd_spec(stories=(story_spec,)))

        jtbd.record_stories(domain.RecordStoriesSpec(story_texts=(_story_text_spec(given="a second story"),)))

        assert [str(story.given) for story in jtbd.stories] == ["the first story"]
