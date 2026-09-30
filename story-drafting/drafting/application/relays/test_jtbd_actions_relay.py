# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestRecordStoriesRequestSnapshot:

    def test_a_record_stories_request_is_its_fields(self) -> None:
        record_stories_request = relays.RecordStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="stories drafted", so_that="I can decide", story_texts=(relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting"),))

        raw = relays.RecordStoriesRequestSnapshot().serialize(record_stories_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "role": "a developer", "i_want": "stories drafted", "so_that": "I can decide", "story_texts": [{"given": "a job to be done", "when": "I submit it", "then": "it is drafting"}]}'

    def test_a_record_stories_request_comes_back_equal(self) -> None:
        record_stories_request_snapshot = relays.RecordStoriesRequestSnapshot()
        record_stories_request = relays.RecordStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="stories drafted", so_that="I can decide", story_texts=(relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting"),))

        returned = record_stories_request_snapshot.deserialize(record_stories_request_snapshot.serialize(record_stories_request))

        assert returned == record_stories_request

    def test_a_record_stories_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1, "role": "a developer", "i_want": "stories drafted", "so_that": "I can decide", "story_texts": [{"given": "a job to be done", "when": "I submit it", "then": "it is drafting"}]}',):
            with pytest.raises(errors.DomainError):
                relays.RecordStoriesRequestSnapshot().deserialize(raw)


class TestRecordStoriesResponseSnapshot:

    def test_a_record_stories_response_is_its_fields(self) -> None:
        record_stories_response = relays.RecordStoriesResponse(jtbd_id="jtbd-1")

        raw = relays.RecordStoriesResponseSnapshot().serialize(record_stories_response)

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_record_stories_response_comes_back_equal(self) -> None:
        record_stories_response_snapshot = relays.RecordStoriesResponseSnapshot()
        record_stories_response = relays.RecordStoriesResponse(jtbd_id="jtbd-1")

        returned = record_stories_response_snapshot.deserialize(record_stories_response_snapshot.serialize(record_stories_response))

        assert returned == record_stories_response

    def test_a_record_stories_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1}',):
            with pytest.raises(errors.DomainError):
                relays.RecordStoriesResponseSnapshot().deserialize(raw)
