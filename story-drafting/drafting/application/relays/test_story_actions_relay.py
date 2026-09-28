from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestWriteStoriesRequestSnapshot:

    def test_a_write_stories_request_round_trips(self) -> None:
        write_stories_request = relays.WriteStoriesRequest(job="ship the release")
        assert (
            relays.WriteStoriesRequestSnapshot().deserialize(relays.WriteStoriesRequestSnapshot().serialize(write_stories_request))
            == write_stories_request
        )

    def test_a_write_stories_request_without_a_job_is_invalid(self) -> None:
        with pytest.raises(errors.DomainError):
            relays.WriteStoriesRequestSnapshot().deserialize(b"{}")


class TestWriteStoriesResponseSnapshot:

    def test_a_write_stories_response_round_trips(self) -> None:
        write_stories_response = relays.WriteStoriesResponse(stories=("a", "b"))
        assert (
            relays.WriteStoriesResponseSnapshot().deserialize(
                relays.WriteStoriesResponseSnapshot().serialize(write_stories_response)
            )
            == write_stories_response
        )

    def test_a_write_stories_response_with_a_story_that_is_not_text_is_invalid(self) -> None:
        with pytest.raises(errors.DomainError):
            relays.WriteStoriesResponseSnapshot().deserialize(b'{"stories": ["a", 1]}')
