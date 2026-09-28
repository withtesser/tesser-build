from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestDraftStoriesRequestSnapshot:

    def test_a_request_is_its_run_id_and_its_job(self) -> None:
        raw = relays.DraftStoriesRequestSnapshot().serialize(relays.DraftStoriesRequest(run_id="r1", job="ship it"))

        assert raw == b'{"run_id": "r1", "job": "ship it"}'

    def test_a_request_comes_back_equal(self) -> None:
        draft_stories_request_snapshot = relays.DraftStoriesRequestSnapshot()
        draft_stories_request = relays.DraftStoriesRequest(run_id="r1", job="ship it")

        returned = draft_stories_request_snapshot.deserialize(
            draft_stories_request_snapshot.serialize(draft_stories_request)
        )

        assert returned == draft_stories_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"run_id": "r1"}', b'{"run_id": "r1", "job": 1}', b'["r1"]'):
            with pytest.raises(errors.DomainError):
                relays.DraftStoriesRequestSnapshot().deserialize(raw)


class TestDraftStoriesResponseSnapshot:

    def test_a_response_is_its_stories(self) -> None:
        raw = relays.DraftStoriesResponseSnapshot().serialize(relays.DraftStoriesResponse(stories=("first", "second")))

        assert raw == b'{"stories": ["first", "second"]}'

    def test_a_response_comes_back_equal(self) -> None:
        draft_stories_response_snapshot = relays.DraftStoriesResponseSnapshot()
        draft_stories_response = relays.DraftStoriesResponse(stories=("first", "second"))

        returned = draft_stories_response_snapshot.deserialize(
            draft_stories_response_snapshot.serialize(draft_stories_response)
        )

        assert returned == draft_stories_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"stories": "first"}', b'{"stories": [1]}', b'["first"]'):
            with pytest.raises(errors.DomainError):
                relays.DraftStoriesResponseSnapshot().deserialize(raw)
