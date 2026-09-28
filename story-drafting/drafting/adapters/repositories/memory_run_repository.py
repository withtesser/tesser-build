from __future__ import annotations

import tesser.adapters as ts

import drafting.application.ports as ports


class MapToRunRecord(ts.Mapper, ports.RunRecord):

    def __init__(self, save_run_request: ports.SaveRunRequest) -> None:
        super().__init__(
            run_id=save_run_request.run_id,
            job=save_run_request.job,
            stage=save_run_request.stage,
            stories=tuple(ports.DraftedStory(text=story) for story in save_run_request.stories),
            accepted_stories=(),
        )


class MapToSaveRunResponse(ts.Mapper, ports.SaveRunResponse):

    def __init__(self, run_record: ports.RunRecord) -> None:
        super().__init__(run_id=run_record.run_id)


class MapToGetRunResponseFromRunRecord(ts.Mapper, ports.GetRunResponse):

    def __init__(self, run_record: ports.RunRecord) -> None:
        super().__init__(outcome=ports.GetRunOutcome.FOUND, runs=(run_record,))


class MapToGetRunResponseFromNothing(ts.Mapper, ports.GetRunResponse):

    def __init__(self) -> None:
        super().__init__(outcome=ports.GetRunOutcome.NOT_FOUND, runs=())


class MemoryRunRepository(ts.Repository):

    def __init__(self) -> None:
        self._runs: dict[str, ports.RunRecord] = {}

    async def save_run(self, save_run_request: ports.SaveRunRequest) -> ports.SaveRunResponse:
        run_record = MapToRunRecord(save_run_request)
        self._runs[save_run_request.run_id] = run_record
        return MapToSaveRunResponse(run_record)

    async def get_run(self, get_run_request: ports.GetRunRequest) -> ports.GetRunResponse:
        run_record = self._runs.get(get_run_request.run_id)
        if run_record is None:
            return MapToGetRunResponseFromNothing()
        return MapToGetRunResponseFromRunRecord(run_record)

    def close(self) -> None:
        self._runs.clear()
