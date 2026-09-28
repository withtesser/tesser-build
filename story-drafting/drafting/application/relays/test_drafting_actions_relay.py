from __future__ import annotations

import drafting.application.relays as relays


class TestKeepDraftedStoriesSnapshots:

    def test_each_message_comes_back_equal(self) -> None:
        keep_drafted_stories_request = relays.KeepDraftedStoriesRequest(
            drafting_id="d1", job="a job", texts=("first", "second")
        )
        keep_drafted_stories_response = relays.KeepDraftedStoriesResponse(drafting_id="d1")

        assert relays.KeepDraftedStoriesRequestSnapshot().deserialize(
            relays.KeepDraftedStoriesRequestSnapshot().serialize(keep_drafted_stories_request)
        ) == keep_drafted_stories_request
        assert relays.KeepDraftedStoriesResponseSnapshot().deserialize(
            relays.KeepDraftedStoriesResponseSnapshot().serialize(keep_drafted_stories_response)
        ) == keep_drafted_stories_response
