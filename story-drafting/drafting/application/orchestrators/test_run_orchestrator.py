from __future__ import annotations

import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays


class TestRunOrchestrator:

    async def test_conducting_a_run_answers_its_run_id(self) -> None:
        conduct_run_response = await orchestrators.RunOrchestrator().conduct_run(
            relays.ConductRunRequest(run_id="r1", job="ship a release")
        )

        assert conduct_run_response.run_id == "r1"
