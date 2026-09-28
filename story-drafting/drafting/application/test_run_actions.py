from __future__ import annotations

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self) -> None:
        self.saved: list[tuple[str, str, str]] = []

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self.saved.append((save_run_request.run_id, save_run_request.job, save_run_request.stage))
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def get_run(self, get_run_request: ports.GetRunRequest) -> ports.GetRunResponse:
        return ports.GetRunResponse(outcome=ports.GetRunOutcome.NOT_FOUND, runs=())


class TestRunActions:

    async def test_keeping_saves_the_run_once_as_drafting_and_answers_its_id(self) -> None:
        fake_run_repository = FakeRunRepository()
        keep_run_response = await application.RunActions(fake_run_repository).keep_run(
            relays.KeepRunRequest(run_id="r1", job="a job")
        )
        assert keep_run_response.run_id == "r1"
        assert fake_run_repository.saved == [("r1", "a job", "drafting")]
