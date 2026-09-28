from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestAwaitPickStoriesResponseSnapshot:

    def test_a_response_is_its_run_id(self) -> None:
        raw = relays.AwaitPickStoriesResponseSnapshot().serialize(relays.AwaitPickStoriesResponse(run_id="r1"))

        assert raw == b'{"run_id": "r1"}'

    def test_a_response_comes_back_equal(self) -> None:
        await_pick_stories_response_snapshot = relays.AwaitPickStoriesResponseSnapshot()
        await_pick_stories_response = relays.AwaitPickStoriesResponse(run_id="r1")

        returned = await_pick_stories_response_snapshot.deserialize(
            await_pick_stories_response_snapshot.serialize(await_pick_stories_response)
        )

        assert returned == await_pick_stories_response

    def test_a_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b'{"run_id": 1}', b'["r1"]'):
            with pytest.raises(errors.DomainError):
                relays.AwaitPickStoriesResponseSnapshot().deserialize(raw)


class TestPickPromise:

    def test_the_pick_promise_is_named_for_the_operation_that_awaits_it(self) -> None:
        assert relays.PICK_STORIES_PROMISE == "pick_stories"
