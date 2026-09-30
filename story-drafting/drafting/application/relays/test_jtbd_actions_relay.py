# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestRecordDraftedStoriesRequestSnapshot:

    def test_a_record_drafted_stories_request_is_its_fields(self) -> None:
        record_drafted_stories_request = relays.RecordDraftedStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", story_texts=(relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),))

        raw = relays.RecordDraftedStoriesRequestSnapshot().serialize(record_drafted_stories_request)

        assert raw == b'{"jtbd_id": "jtbd-1", "role": "a developer", "i_want": "my checkpoints fixed in advance", "so_that": "I can step away and come back", "story_texts": [{"given": "a job to be done", "when": "I submit it", "then": "it is drafting its stories"}]}'

    def test_a_record_drafted_stories_request_comes_back_equal(self) -> None:
        record_drafted_stories_request_snapshot = relays.RecordDraftedStoriesRequestSnapshot()
        record_drafted_stories_request = relays.RecordDraftedStoriesRequest(jtbd_id="jtbd-1", role="a developer", i_want="my checkpoints fixed in advance", so_that="I can step away and come back", story_texts=(relays.JtbdActionsStoryText(given="a job to be done", when="I submit it", then="it is drafting its stories"),))

        returned = record_drafted_stories_request_snapshot.deserialize(record_drafted_stories_request_snapshot.serialize(record_drafted_stories_request))

        assert returned == record_drafted_stories_request

    def test_a_record_drafted_stories_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1, "role": "a developer", "i_want": "my checkpoints fixed in advance", "so_that": "I can step away and come back", "story_texts": [{"given": "a job to be done", "when": "I submit it", "then": "it is drafting its stories"}]}',):
            with pytest.raises(errors.DomainError):
                relays.RecordDraftedStoriesRequestSnapshot().deserialize(raw)


class TestRecordDraftedStoriesResponseSnapshot:

    def test_a_record_drafted_stories_response_is_its_fields(self) -> None:
        record_drafted_stories_response = relays.RecordDraftedStoriesResponse(jtbd_id="jtbd-1")

        raw = relays.RecordDraftedStoriesResponseSnapshot().serialize(record_drafted_stories_response)

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_record_drafted_stories_response_comes_back_equal(self) -> None:
        record_drafted_stories_response_snapshot = relays.RecordDraftedStoriesResponseSnapshot()
        record_drafted_stories_response = relays.RecordDraftedStoriesResponse(jtbd_id="jtbd-1")

        returned = record_drafted_stories_response_snapshot.deserialize(record_drafted_stories_response_snapshot.serialize(record_drafted_stories_response))

        assert returned == record_drafted_stories_response

    def test_a_record_drafted_stories_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1}',):
            with pytest.raises(errors.DomainError):
                relays.RecordDraftedStoriesResponseSnapshot().deserialize(raw)
