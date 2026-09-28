from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunActionsRelay(relays.RunActionsRelay):

    def __init__(self) -> None:
        self.recorded: list[str] = []

    async def run_record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        self.recorded.append(str(record_run_request.run.identity))
        return relays.RecordRunResponse(run_id=str(record_run_request.run.identity))


class TestRunOrchestrator:

    async def test_drafting_stories_records_the_run_it_was_started_on(self) -> None:
        fake_run_actions_relay = FakeRunActionsRelay()
        run = domain.Run(domain.RunSpec(run_id="r1", job="ship", stage="drafting", stories=(), accepted_stories=()))
        draft_stories_response = await orchestrators.RunOrchestrator(fake_run_actions_relay).draft_stories(
            relays.DraftStoriesRequest(run=run)
        )
        assert draft_stories_response.run_id == "r1"
        assert fake_run_actions_relay.recorded == ["r1"]
