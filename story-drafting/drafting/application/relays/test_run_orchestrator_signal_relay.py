from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestAwaitPickStoriesResponseSnapshot:

    def test_a_pick_is_the_stories_picked(self) -> None:
        raw = relays.AwaitPickStoriesResponseSnapshot().serialize(relays.AwaitPickStoriesResponse(stories=("a",)))

        assert raw == b'{"stories": ["a"]}'

    def test_a_pick_comes_back_equal(self) -> None:
        await_pick_stories_response_snapshot = relays.AwaitPickStoriesResponseSnapshot()
        await_pick_stories_response = relays.AwaitPickStoriesResponse(stories=("a", "b"))

        returned = await_pick_stories_response_snapshot.deserialize(
            await_pick_stories_response_snapshot.serialize(await_pick_stories_response)
        )

        assert returned == await_pick_stories_response

    def test_a_pick_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"stories": "a"}', b'{"stories": [1]}', b'["a"]'):
            with pytest.raises(errors.DomainError):
                relays.AwaitPickStoriesResponseSnapshot().deserialize(raw)

    def test_the_promise_is_named_for_the_pick(self) -> None:
        assert relays.PICK_STORIES_PROMISE == "pick_stories"
