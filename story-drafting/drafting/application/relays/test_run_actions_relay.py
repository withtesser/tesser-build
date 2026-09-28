from __future__ import annotations

import drafting.application.relays as relays


class TestKeepRunSnapshots:

    def test_each_message_comes_back_equal(self) -> None:
        keep_run_request = relays.KeepRunRequest(run_id="r1", job="a job")
        keep_run_response = relays.KeepRunResponse(run_id="r1")
        assert relays.KeepRunRequestSnapshot().deserialize(
            relays.KeepRunRequestSnapshot().serialize(keep_run_request)
        ) == keep_run_request
        assert relays.KeepRunResponseSnapshot().deserialize(
            relays.KeepRunResponseSnapshot().serialize(keep_run_response)
        ) == keep_run_response


class TestOfferStoriesSnapshots:

    def test_each_message_comes_back_equal(self) -> None:
        offer_stories_request = relays.OfferStoriesRequest(run_id="r1", job="a job", stories=("a story", "another story"))
        offer_stories_response = relays.OfferStoriesResponse(run_id="r1")
        assert relays.OfferStoriesRequestSnapshot().deserialize(
            relays.OfferStoriesRequestSnapshot().serialize(offer_stories_request)
        ) == offer_stories_request
        assert relays.OfferStoriesResponseSnapshot().deserialize(
            relays.OfferStoriesResponseSnapshot().serialize(offer_stories_response)
        ) == offer_stories_response
