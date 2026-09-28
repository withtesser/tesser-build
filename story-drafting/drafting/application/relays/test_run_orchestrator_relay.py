from __future__ import annotations

import pytest

import drafting.application.relays as relays
import drafting.domain as domain
import tesser.errors as errors


class TestDraftStoriesRequestSnapshot:

    def test_a_draft_stories_request_carries_its_run_across(self) -> None:
        run = domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=()))
        draft_stories_request = relays.DraftStoriesRequestSnapshot().deserialize(
            relays.DraftStoriesRequestSnapshot().serialize(relays.DraftStoriesRequest(run=run))
        )
        assert draft_stories_request.run.identity == run.identity
        assert draft_stories_request.run.job == run.job


class TestDraftStoriesResponseSnapshot:

    def test_a_draft_stories_response_round_trips(self) -> None:
        draft_stories_response = relays.DraftStoriesResponse(run_id="r1")
        assert (
            relays.DraftStoriesResponseSnapshot().deserialize(
                relays.DraftStoriesResponseSnapshot().serialize(draft_stories_response)
            )
            == draft_stories_response
        )

    def test_a_draft_stories_response_without_a_run_id_is_invalid(self) -> None:
        with pytest.raises(errors.DomainError):
            relays.DraftStoriesResponseSnapshot().deserialize(b"[]")
