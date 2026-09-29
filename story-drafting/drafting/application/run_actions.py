from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.domain as domain


class MapToSaveRunRequest(ts.Mapper, ports.SaveRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(
            run_id=str(run.identity),
            job=str(run.job),
            stage=str(run.stage),
            stories=tuple(str(story) for story in run.stories),
            accepted_stories=tuple(str(story) for story in run.accepted_stories),
        )


class MapToRecordRunResponse(ts.Mapper, relays.RecordRunResponse):

    def __init__(self, save_run_response: ports.SaveRunResponse) -> None:
        super().__init__(run_id=save_run_response.run_id)


class RunActions(ts.Actions):

    def __init__(self, run_store: ports.RunStore) -> None:
        self._run_store = run_store

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        run = record_run_request.run
        async with self._run_store.transaction() as run_repository:
            save_run_response = await run_repository.save_run(MapToSaveRunRequest(run))
        return MapToRecordRunResponse(save_run_response)
