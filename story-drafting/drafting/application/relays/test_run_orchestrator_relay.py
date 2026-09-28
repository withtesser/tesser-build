from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestDraftStoriesRequestSnapshot:

    def test_a_request_is_its_fields(self) -> None:
        draft_stories_request = relays.DraftStoriesRequest(run_id="run-1", job="plan a migration", stage="drafting")

        raw = relays.DraftStoriesRequestSnapshot().serialize(draft_stories_request)

        assert raw == b'{"run_id": "run-1", "job": "plan a migration", "stage": "drafting"}'

    def test_a_request_comes_back_equal(self) -> None:
        draft_stories_request_snapshot = relays.DraftStoriesRequestSnapshot()
        draft_stories_request = relays.DraftStoriesRequest(run_id="run-1", job="plan a migration", stage="drafting")

        returned = draft_stories_request_snapshot.deserialize(
            draft_stories_request_snapshot.serialize(draft_stories_request)
        )

        assert returned == draft_stories_request

    def test_a_request_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (
            b"{}",
            b'{"run_id": 1, "job": "plan a migration", "stage": "drafting"}',
            b'{"run_id": "run-1", "job": "plan a migration"}',
            b'["run-1"]',
        ):
            with pytest.raises(errors.DomainError):
                relays.DraftStoriesRequestSnapshot().deserialize(raw)


class TestDraftStoriesResponseSnapshot:

    def test_a_response_is_its_run_id(self) -> None:
        raw = relays.DraftStoriesResponseSnapshot().serialize(relays.DraftStoriesResponse(run_id="run-1"))

        assert raw == b'{"run_id": "run-1"}'

    def test_a_response_comes_back_equal(self) -> None:
        draft_stories_response_snapshot = relays.DraftStoriesResponseSnapshot()
        draft_stories_response = relays.DraftStoriesResponse(run_id="run-1")

        returned = draft_stories_response_snapshot.deserialize(
            draft_stories_response_snapshot.serialize(draft_stories_response)
        )

        assert returned == draft_stories_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"run_id": 1}', b'["run-1"]'):
            with pytest.raises(errors.DomainError):
                relays.DraftStoriesResponseSnapshot().deserialize(raw)
