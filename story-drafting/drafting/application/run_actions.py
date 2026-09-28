from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays


class MapToSaveRunRequest(ts.Mapper, ports.SaveRunRequest):

    def __init__(self, record_run_request: relays.RecordRunRequest) -> None:
        super().__init__(
            run_id=record_run_request.run_id,
            job=record_run_request.job,
            stage=record_run_request.stage,
        )


class MapToRecordRunResponse(ts.Mapper, relays.RecordRunResponse):

    def __init__(self, save_run_response: ports.SaveRunResponse) -> None:
        super().__init__(run_id=save_run_response.run_id)


class RunActions(ts.Actions):

    def __init__(self, run_store: ports.RunStore) -> None:
        self._run_store = run_store

    async def record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        async with self._run_store.transaction() as run_repository:
            save_run_response = await run_repository.save_run(MapToSaveRunRequest(record_run_request))
        return MapToRecordRunResponse(save_run_response)
