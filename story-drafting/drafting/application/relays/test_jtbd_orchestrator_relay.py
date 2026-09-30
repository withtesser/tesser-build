# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestStoryDraftingRequestSnapshot:

    def test_a_story_drafting_request_is_its_fields(self) -> None:
        story_drafting_request = relays.StoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back")

        raw = relays.StoryDraftingRequestSnapshot().serialize(story_drafting_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "role": "a developer", "i_want": "my checkpoints fixed in advance", "so_that": "I can step away and come back"}'

    def test_a_story_drafting_request_comes_back_equal(self) -> None:
        story_drafting_request_snapshot = relays.StoryDraftingRequestSnapshot()
        story_drafting_request = relays.StoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back")

        returned = story_drafting_request_snapshot.deserialize(story_drafting_request_snapshot.serialize(story_drafting_request))

        assert returned == story_drafting_request

    def test_a_story_drafting_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1, "role": "a developer", "i_want": "my checkpoints fixed in advance", "so_that": "I can step away and come back"}',):
            with pytest.raises(errors.DomainError):
                relays.StoryDraftingRequestSnapshot().deserialize(raw)


class TestStoryDraftingResponseSnapshot:

    def test_a_story_drafting_response_is_its_fields(self) -> None:
        story_drafting_response = relays.StoryDraftingResponse(jtbd_id="jtbd-1")

        raw = relays.StoryDraftingResponseSnapshot().serialize(story_drafting_response)

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_story_drafting_response_comes_back_equal(self) -> None:
        story_drafting_response_snapshot = relays.StoryDraftingResponseSnapshot()
        story_drafting_response = relays.StoryDraftingResponse(jtbd_id="jtbd-1")

        returned = story_drafting_response_snapshot.deserialize(story_drafting_response_snapshot.serialize(story_drafting_response))

        assert returned == story_drafting_response

    def test_a_story_drafting_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1}',):
            with pytest.raises(errors.DomainError):
                relays.StoryDraftingResponseSnapshot().deserialize(raw)
