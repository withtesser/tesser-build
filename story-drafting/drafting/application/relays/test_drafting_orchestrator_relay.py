from __future__ import annotations

import drafting.application.relays as relays


class TestDraftingOrchestratorSnapshots:

    def test_each_message_comes_back_equal(self) -> None:
        conduct_drafting_request = relays.ConductDraftingRequest(drafting_id="d1", job="a job")
        conduct_drafting_response = relays.ConductDraftingResponse(drafting_id="d1")

        assert relays.ConductDraftingRequestSnapshot().deserialize(
            relays.ConductDraftingRequestSnapshot().serialize(conduct_drafting_request)
        ) == conduct_drafting_request
        assert relays.ConductDraftingResponseSnapshot().deserialize(
            relays.ConductDraftingResponseSnapshot().serialize(conduct_drafting_response)
        ) == conduct_drafting_response
