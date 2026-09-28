from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import drafting.application as application
import drafting.application.ports as ports
import drafting.application.relays as relays


@ts.fake
class FakeRunRepository(ports.RunRepository):

    def __init__(self, runs: dict[str, ports.Run]) -> None:
        self._runs = runs

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        self._runs[save_run_request.run_id] = ports.Run(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            stage=save_run_request.stage,
            stories=save_run_request.stories,
            accepted_stories=save_run_request.accepted_stories,
        )
        return ports.SaveRunResponse(run_id=save_run_request.run_id)

    async def load_run(self, load_run_request: ports.LoadRunRequest) -> ports.LoadRunResponse:
        return ports.LoadRunResponse(runs=(self._runs[load_run_request.run_id],))


@ts.fake
class FakeRunStore(ports.RunStore):

    def __init__(self) -> None:
        self.runs: dict[str, ports.Run] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.RunRepository]:
        yield FakeRunRepository(self.runs)


class TestRunActions:

    async def test_record_run_saves_the_run_under_its_run_id(self) -> None:
        fake_run_store = FakeRunStore()
        run_actions = application.RunActions(fake_run_store)

        await run_actions.record_run(
            relays.RecordRunRequest(
                run_id="run-1", job="plan a migration", stage="awaiting_pick", stories=("a story",), accepted_stories=()
            )
        )

        assert fake_run_store.runs["run-1"] == ports.Run(
            run_id="run-1", job="plan a migration", stage="awaiting_pick", stories=("a story",), accepted_stories=()
        )

    async def test_record_run_answers_the_run_id_it_saved(self) -> None:
        run_actions = application.RunActions(FakeRunStore())

        record_run_response = await run_actions.record_run(
            relays.RecordRunRequest(
                run_id="run-1", job="plan a migration", stage="awaiting_pick", stories=("a story",), accepted_stories=()
            )
        )

        assert record_run_response.run_id == "run-1"
