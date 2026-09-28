from __future__ import annotations

import drafting.application.relays as relays
import drafting.domain as domain


class TestDraftStoriesSnapshots:

    def test_each_message_comes_back_equal(self) -> None:
        draft_stories_request = relays.DraftStoriesRequest(run_id=domain.RunId("r1"), job=domain.Job("a job"))
        draft_stories_response = relays.DraftStoriesResponse(run_id="r1")
        assert relays.DraftStoriesRequestSnapshot().deserialize(
            relays.DraftStoriesRequestSnapshot().serialize(draft_stories_request)
        ) == draft_stories_request
        assert relays.DraftStoriesResponseSnapshot().deserialize(
            relays.DraftStoriesResponseSnapshot().serialize(draft_stories_response)
        ) == draft_stories_response

    def test_the_request_carries_the_run_id_and_the_job_by_name(self) -> None:
        draft_stories_request = relays.DraftStoriesRequest(run_id=domain.RunId("r1"), job=domain.Job("a job"))
        assert relays.DraftStoriesRequestSnapshot().serialize(draft_stories_request) == (
            b'{"run_id": "r1", "job": "a job"}'
        )
