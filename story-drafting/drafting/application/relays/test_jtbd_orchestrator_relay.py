# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestDraftJtbdStoriesRequestSnapshot:

    def test_a_draft_jtbd_stories_request_is_its_fields(self) -> None:
        draft_jtbd_stories_request = relays.DraftJtbdStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="to keep my place", so_that="I can step away")

        raw = relays.DraftJtbdStoriesRequestSnapshot().serialize(draft_jtbd_stories_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "role": "a developer", "i_want": "to keep my place", "so_that": "I can step away"}'

    def test_a_draft_jtbd_stories_request_comes_back_equal(self) -> None:
        draft_jtbd_stories_request_snapshot = relays.DraftJtbdStoriesRequestSnapshot()
        draft_jtbd_stories_request = relays.DraftJtbdStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="to keep my place", so_that="I can step away")

        returned = draft_jtbd_stories_request_snapshot.deserialize(draft_jtbd_stories_request_snapshot.serialize(draft_jtbd_stories_request))

        assert returned == draft_jtbd_stories_request

    def test_a_draft_jtbd_stories_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1, "role": "a developer", "i_want": "to keep my place", "so_that": "I can step away"}',):
            with pytest.raises(errors.DomainError):
                relays.DraftJtbdStoriesRequestSnapshot().deserialize(raw)


class TestDraftJtbdStoriesResponseSnapshot:

    def test_a_draft_jtbd_stories_response_is_its_fields(self) -> None:
        draft_jtbd_stories_response = relays.DraftJtbdStoriesResponse(jtbd_id="jtbd-1")

        raw = relays.DraftJtbdStoriesResponseSnapshot().serialize(draft_jtbd_stories_response)

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_draft_jtbd_stories_response_comes_back_equal(self) -> None:
        draft_jtbd_stories_response_snapshot = relays.DraftJtbdStoriesResponseSnapshot()
        draft_jtbd_stories_response = relays.DraftJtbdStoriesResponse(jtbd_id="jtbd-1")

        returned = draft_jtbd_stories_response_snapshot.deserialize(draft_jtbd_stories_response_snapshot.serialize(draft_jtbd_stories_response))

        assert returned == draft_jtbd_stories_response

    def test_a_draft_jtbd_stories_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1}',):
            with pytest.raises(errors.DomainError):
                relays.DraftJtbdStoriesResponseSnapshot().deserialize(raw)
