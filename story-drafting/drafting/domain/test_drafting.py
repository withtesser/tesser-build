from __future__ import annotations

import pytest

import tesser.testing as ts

import drafting.domain as domain
import tesser.errors as errors


@ts.helper
def _story_spec(story_id: str = "1", text: str = "As a developer, I want a pick") -> domain.StorySpec:
    return domain.StorySpec(story_id=story_id, text=text)


@ts.helper
def _drafting_spec(
    drafting_id: str = "d1",
    job: str = "a job",
    step: str = "drafting",
    stories: tuple[domain.StorySpec, ...] = (),
    accepted_stories: tuple[domain.StorySpec, ...] = (),
) -> domain.DraftingSpec:
    return domain.DraftingSpec(
        drafting_id=drafting_id, job=job, step=step, stories=stories, accepted_stories=accepted_stories
    )


class TestDrafting:

    def test_a_drafting_constructs_from_its_spec(self) -> None:
        drafting_spec = _drafting_spec(
            step="awaiting_pick", stories=(_story_spec(story_id="1"), _story_spec(story_id="2")),
            accepted_stories=(_story_spec(story_id="2"),),
        )

        drafting = domain.Drafting(drafting_spec)

        assert str(drafting.identity) == drafting_spec.drafting_id
        assert str(drafting.job) == drafting_spec.job
        assert str(drafting.step) == drafting_spec.step
        assert [(str(story.identity), str(story.text)) for story in drafting.stories] == [
            (story_spec.story_id, story_spec.text) for story_spec in drafting_spec.stories
        ]
        assert [(str(story.identity), str(story.text)) for story in drafting.accepted_stories] == [
            (story_spec.story_id, story_spec.text) for story_spec in drafting_spec.accepted_stories
        ]

    def test_drafting_numbers_the_drafted_stories_and_awaits_the_pick(self) -> None:
        drafting = domain.Drafting(_drafting_spec(step="drafting"))

        drafting.draft(domain.DraftedStories(domain.DraftedStoriesSpec(texts=("first", "second"))))

        assert str(drafting.step) == "awaiting_pick"
        assert [(str(story.identity), str(story.text)) for story in drafting.stories] == [
            ("1", "first"),
            ("2", "second"),
        ]

    def test_drafting_accepts_no_story(self) -> None:
        drafting = domain.Drafting(_drafting_spec(step="drafting"))

        drafting.draft(domain.DraftedStories(domain.DraftedStoriesSpec(texts=("first",))))

        assert drafting.accepted_stories == ()


    def test_a_drafting_drafts_its_stories_once(self) -> None:
        drafting = domain.Drafting(_drafting_spec(step="awaiting_pick", stories=(_story_spec(),)))

        with pytest.raises(errors.DomainError):
            drafting.draft(domain.DraftedStories(domain.DraftedStoriesSpec(texts=("again",))))

    def test_a_drafting_still_drafting_with_stories_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Drafting(_drafting_spec(step="drafting", stories=(_story_spec(),)))

    def test_a_drafting_awaiting_the_pick_with_no_stories_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Drafting(_drafting_spec(step="awaiting_pick", stories=()))

    def test_an_accepted_story_that_was_not_drafted_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Drafting(
                _drafting_spec(
                    step="awaiting_pick",
                    stories=(_story_spec(story_id="1"),),
                    accepted_stories=(_story_spec(story_id="2"),),
                )
            )


class TestDraftingId:

    def test_a_drafting_id_equals_by_value(self) -> None:
        assert domain.DraftingId("d1") == domain.DraftingId("d1")
        assert domain.DraftingId("d1") != domain.DraftingId("d2")

    def test_an_empty_drafting_id_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.DraftingId("")


class TestJob:

    def test_a_job_equals_by_value(self) -> None:
        assert domain.Job("a job") == domain.Job(" a job ")
        assert domain.Job("a job") != domain.Job("another job")

    def test_a_blank_job_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Job("  ")


class TestStep:

    def test_a_step_equals_by_value(self) -> None:
        assert domain.Step("drafting") == domain.Step("drafting")
        assert domain.Step("drafting") != domain.Step("awaiting_pick")

    def test_a_step_outside_the_set_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.Step("picked_by_the_agent")


class TestStoryId:

    def test_a_story_id_equals_by_value(self) -> None:
        assert domain.StoryId("1") == domain.StoryId("1")
        assert domain.StoryId("1") != domain.StoryId("2")

    def test_an_empty_story_id_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.StoryId("")


class TestStoryText:

    def test_a_story_text_equals_by_value(self) -> None:
        assert domain.StoryText("a story") == domain.StoryText("a story ")
        assert domain.StoryText("a story") != domain.StoryText("another story")

    def test_a_blank_story_text_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.StoryText("")


class TestDraftedStories:

    def test_drafted_stories_equal_by_value(self) -> None:
        assert domain.DraftedStories(domain.DraftedStoriesSpec(texts=("a",))) == domain.DraftedStories(
            domain.DraftedStoriesSpec(texts=("a ",))
        )
        assert domain.DraftedStories(domain.DraftedStoriesSpec(texts=("a",))) != domain.DraftedStories(
            domain.DraftedStoriesSpec(texts=("b",))
        )

    def test_drafted_stories_construct_from_their_spec(self) -> None:
        drafted_stories_spec = domain.DraftedStoriesSpec(texts=("a", "b"))

        drafted_stories = domain.DraftedStories(drafted_stories_spec)

        assert tuple(str(text) for text in drafted_stories.texts) == drafted_stories_spec.texts

    def test_drafting_no_story_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.DraftedStories(domain.DraftedStoriesSpec(texts=()))


class TestStory:

    def test_a_story_constructs_from_its_spec(self) -> None:
        story_spec = _story_spec(story_id="3", text="a story")

        story = domain.Story(story_spec)

        assert (str(story.identity), str(story.text)) == (story_spec.story_id, story_spec.text)


class TestDraftingPresence:

    def test_a_drafting_found_decides_found(self) -> None:
        assert domain.DraftingPresence(domain.DraftingPresenceSpec(presence="found")).decide() is domain.DraftingLookup.FOUND

    def test_a_drafting_not_found_decides_not_found(self) -> None:
        assert (
            domain.DraftingPresence(domain.DraftingPresenceSpec(presence="not_found")).decide()
            is domain.DraftingLookup.NOT_FOUND
        )

    def test_a_presence_outside_the_set_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            domain.DraftingPresence(domain.DraftingPresenceSpec(presence="maybe"))

    def test_a_presence_equals_by_value(self) -> None:
        assert domain.DraftingPresence(domain.DraftingPresenceSpec(presence="found")) == domain.DraftingPresence(
            domain.DraftingPresenceSpec(presence="found")
        )
        assert domain.DraftingPresence(domain.DraftingPresenceSpec(presence="found")) != domain.DraftingPresence(
            domain.DraftingPresenceSpec(presence="not_found")
        )
