# pragma: tesser-generated; regenerate from the composition, never edit by hand
from __future__ import annotations

import pytest

import drafting.application.relays as relays
import tesser.errors as errors


class TestAwaitAcceptStoriesResponseSnapshot:

    def test_a_await_accept_stories_response_is_its_fields(self) -> None:
        await_accept_stories_response = relays.AwaitAcceptStoriesResponse(jtbd_id="jtbd-1")

        raw = relays.AwaitAcceptStoriesResponseSnapshot().serialize(await_accept_stories_response)

        assert raw == b'{"jtbd_id": "jtbd-1"}'

    def test_a_await_accept_stories_response_comes_back_equal(self) -> None:
        await_accept_stories_response_snapshot = relays.AwaitAcceptStoriesResponseSnapshot()
        await_accept_stories_response = relays.AwaitAcceptStoriesResponse(jtbd_id="jtbd-1")

        returned = await_accept_stories_response_snapshot.deserialize(await_accept_stories_response_snapshot.serialize(await_accept_stories_response))

        assert returned == await_accept_stories_response

    def test_a_await_accept_stories_response_of_the_wrong_shape_is_refused_before_the_constructor(self) -> None:
        for raw in (b"{}", b"[]", b'{"jtbd_id": 1}',):
            with pytest.raises(errors.DomainError):
                relays.AwaitAcceptStoriesResponseSnapshot().deserialize(raw)
