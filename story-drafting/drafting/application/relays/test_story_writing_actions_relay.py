from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestWriteStoriesRequestSnapshot:

    def test_a_request_is_its_job(self) -> None:
        raw = relays.WriteStoriesRequestSnapshot().serialize(relays.WriteStoriesRequest(job="plan a migration"))

        assert raw == b'{"job": "plan a migration"}'

    def test_a_request_comes_back_equal(self) -> None:
        write_stories_request_snapshot = relays.WriteStoriesRequestSnapshot()
        write_stories_request = relays.WriteStoriesRequest(job="plan a migration")

        returned = write_stories_request_snapshot.deserialize(
            write_stories_request_snapshot.serialize(write_stories_request)
        )

        assert returned == write_stories_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"job": 1}', b'["plan a migration"]'):
            with pytest.raises(errors.DomainError):
                relays.WriteStoriesRequestSnapshot().deserialize(raw)


class TestWriteStoriesResponseSnapshot:

    def test_a_response_is_its_stories(self) -> None:
        raw = relays.WriteStoriesResponseSnapshot().serialize(relays.WriteStoriesResponse(stories=("a", "b")))

        assert raw == b'{"stories": ["a", "b"]}'

    def test_a_response_comes_back_equal(self) -> None:
        write_stories_response_snapshot = relays.WriteStoriesResponseSnapshot()
        write_stories_response = relays.WriteStoriesResponse(stories=("a", "b"))

        returned = write_stories_response_snapshot.deserialize(
            write_stories_response_snapshot.serialize(write_stories_response)
        )

        assert returned == write_stories_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"stories": "a"}', b'{"stories": [1]}', b'["a"]'):
            with pytest.raises(errors.DomainError):
                relays.WriteStoriesResponseSnapshot().deserialize(raw)
