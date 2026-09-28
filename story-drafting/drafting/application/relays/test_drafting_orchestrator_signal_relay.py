from __future__ import annotations

import drafting.application.relays as relays


class TestAwaitPickStoryResponseSnapshot:

    def test_the_promise_named_for_its_operation_carries_the_story_picked(self) -> None:
        await_pick_story_response = relays.AwaitPickStoryResponse(story_id="1")
        await_pick_story_response_snapshot = relays.AwaitPickStoryResponseSnapshot()

        assert relays.PICK_STORY_PROMISE == "pick_story"
        assert await_pick_story_response_snapshot.deserialize(
            await_pick_story_response_snapshot.serialize(await_pick_story_response)
        ) == await_pick_story_response
