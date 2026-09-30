# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestConductStoryDraftingRequestSnapshot:

    def test_a_conduct_story_drafting_request_is_its_fields(self) -> None:
        conduct_story_drafting_request = relays.ConductStoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away")

        raw = relays.ConductStoryDraftingRequestSnapshot().serialize(conduct_story_drafting_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "role": "a developer", "i_want": "my steps fixed in advance", "so_that": "I can step away"}'

    def test_a_conduct_story_drafting_request_comes_back_equal(self) -> None:
        conduct_story_drafting_request_snapshot = relays.ConductStoryDraftingRequestSnapshot()
        conduct_story_drafting_request = relays.ConductStoryDraftingRequest(jtbd_id="jtbd-1", role="a developer", i_want="my steps fixed in advance", so_that="I can step away")

        returned = conduct_story_drafting_request_snapshot.deserialize(conduct_story_drafting_request_snapshot.serialize(conduct_story_drafting_request))

        assert returned == conduct_story_drafting_request

    def test_a_conduct_story_drafting_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1, "role": "a developer", "i_want": "my steps fixed in advance", "so_that": "I can step away"}',):
            with pytest.raises(errors.DomainError):
                relays.ConductStoryDraftingRequestSnapshot().deserialize(raw)


class TestConductStoryDraftingResponseSnapshot:

    def test_a_conduct_story_drafting_response_is_its_fields(self) -> None:
        conduct_story_drafting_response = relays.ConductStoryDraftingResponse(jtbd_id="jtbd-1")

        raw = relays.ConductStoryDraftingResponseSnapshot().serialize(conduct_story_drafting_response)

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_conduct_story_drafting_response_comes_back_equal(self) -> None:
        conduct_story_drafting_response_snapshot = relays.ConductStoryDraftingResponseSnapshot()
        conduct_story_drafting_response = relays.ConductStoryDraftingResponse(jtbd_id="jtbd-1")

        returned = conduct_story_drafting_response_snapshot.deserialize(conduct_story_drafting_response_snapshot.serialize(conduct_story_drafting_response))

        assert returned == conduct_story_drafting_response

    def test_a_conduct_story_drafting_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1}',):
            with pytest.raises(errors.DomainError):
                relays.ConductStoryDraftingResponseSnapshot().deserialize(raw)
