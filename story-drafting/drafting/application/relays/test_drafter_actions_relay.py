from __future__ import annotations

import drafting.application.relays as relays


class TestWriteStoriesSnapshots:

    def test_each_message_comes_back_equal(self) -> None:
        write_stories_request = relays.WriteStoriesRequest(job="a job")
        write_stories_response = relays.WriteStoriesResponse(stories=("a story", "another story"))
        assert relays.WriteStoriesRequestSnapshot().deserialize(
            relays.WriteStoriesRequestSnapshot().serialize(write_stories_request)
        ) == write_stories_request
        assert relays.WriteStoriesResponseSnapshot().deserialize(
            relays.WriteStoriesResponseSnapshot().serialize(write_stories_response)
        ) == write_stories_response
