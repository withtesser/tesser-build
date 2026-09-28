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
