from __future__ import annotations

import drafting.application.relays as relays


class TestAwaitPickStoriesResponseSnapshot:

    def test_the_promise_named_for_its_operation_carries_the_run_it_was_picked_for(self) -> None:
        await_pick_stories_response = relays.AwaitPickStoriesResponse(run_id="r1")
        await_pick_stories_response_snapshot = relays.AwaitPickStoriesResponseSnapshot()
        assert relays.PICK_STORIES_PROMISE == "pick_stories"
        assert await_pick_stories_response_snapshot.deserialize(
            await_pick_stories_response_snapshot.serialize(await_pick_stories_response)
        ) == await_pick_stories_response
