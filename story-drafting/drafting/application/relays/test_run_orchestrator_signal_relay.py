from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestAwaitPickStoryResponseSnapshot:

    def test_an_await_pick_story_response_round_trips(self) -> None:
        await_pick_story_response = relays.AwaitPickStoryResponse(run_id="r1")
        assert (
            relays.AwaitPickStoryResponseSnapshot().deserialize(
                relays.AwaitPickStoryResponseSnapshot().serialize(await_pick_story_response)
            )
            == await_pick_story_response
        )

    def test_an_await_pick_story_response_without_a_run_id_is_invalid(self) -> None:
        with pytest.raises(errors.DomainError):
            relays.AwaitPickStoryResponseSnapshot().deserialize(b"{}")
