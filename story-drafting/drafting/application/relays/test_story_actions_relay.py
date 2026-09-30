# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestDraftStoriesRequestSnapshot:

    def test_a_draft_stories_request_is_its_fields(self) -> None:
        draft_stories_request = relays.DraftStoriesRequest(role="a developer", i_want="stories drafted for my job to be done", so_that="I can decide which to keep")

        raw = relays.DraftStoriesRequestSnapshot().serialize(draft_stories_request)

        assert raw == b'{"role": "a developer", "i_want": "stories drafted for my job to be done", "so_that": "I can decide which to keep"}'

    def test_a_draft_stories_request_comes_back_equal(self) -> None:
        draft_stories_request_snapshot = relays.DraftStoriesRequestSnapshot()
        draft_stories_request = relays.DraftStoriesRequest(role="a developer", i_want="stories drafted for my job to be done", so_that="I can decide which to keep")

        returned = draft_stories_request_snapshot.deserialize(draft_stories_request_snapshot.serialize(draft_stories_request))

        assert returned == draft_stories_request

    def test_a_draft_stories_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"role": 1, "i_want": "stories drafted for my job to be done", "so_that": "I can decide which to keep"}',):
            with pytest.raises(errors.DomainError):
                relays.DraftStoriesRequestSnapshot().deserialize(raw)


class TestDraftStoriesResponseSnapshot:

    def test_a_draft_stories_response_is_its_fields(self) -> None:
        draft_stories_response = relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),))

        raw = relays.DraftStoriesResponseSnapshot().serialize(draft_stories_response)

        assert raw == b'{"story_texts": [{"given": "a job to be done", "when": "I submit it", "then": "it is drafting its stories"}]}'

    def test_a_draft_stories_response_comes_back_equal(self) -> None:
        draft_stories_response_snapshot = relays.DraftStoriesResponseSnapshot()
        draft_stories_response = relays.DraftStoriesResponse(story_texts=(relays.StoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),))

        returned = draft_stories_response_snapshot.deserialize(draft_stories_response_snapshot.serialize(draft_stories_response))

        assert returned == draft_stories_response

    def test_a_draft_stories_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"story_texts": 1}',):
            with pytest.raises(errors.DomainError):
                relays.DraftStoriesResponseSnapshot().deserialize(raw)
