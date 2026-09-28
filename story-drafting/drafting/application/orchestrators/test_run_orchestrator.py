from __future__ import annotations

import tesser.testing as ts

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays
import drafting.domain as domain


@ts.fake
class FakeRunActionsRelay(relays.RunActionsRelay):

    def __init__(self) -> None:
        self.kept: list[tuple[str, str]] = []

    async def run_keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
        self.kept.append((keep_run_request.run_id, keep_run_request.job))
        return relays.KeepRunResponse(run_id=keep_run_request.run_id)


class TestRunOrchestrator:

    async def test_drafting_stories_keeps_the_run_and_answers_its_id(self) -> None:
        fake_run_actions_relay = FakeRunActionsRelay()
        draft_stories_response = await orchestrators.RunOrchestrator(fake_run_actions_relay).draft_stories(
            relays.DraftStoriesRequest(run_id=domain.RunId("r1"), job=domain.Job("a job"))
        )
        assert draft_stories_response.run_id == "r1"
        assert fake_run_actions_relay.kept == [("r1", "a job")]
