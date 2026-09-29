from __future__ import annotations

import tesser.application as ts

import story_drafting.application.ports as ports
import story_drafting.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, record_jtbd_request: relays.RecordJtbdRequest) -> None:
        super().__init__(
            jtbd_id=record_jtbd_request.jtbd_id,
            statement=record_jtbd_request.statement,
            step=record_jtbd_request.step,
            draft_count=record_jtbd_request.draft_count,
            picked_draft=record_jtbd_request.picked_draft,
        )


class MapToRecordJtbdResponse(ts.Mapper, relays.RecordJtbdResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JobToBeDoneActions(ts.Actions):

    def __init__(self, job_to_be_done_store: ports.JobToBeDoneStore) -> None:
        self._job_to_be_done_store = job_to_be_done_store

    async def record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse:
        async with self._job_to_be_done_store.transaction() as job_to_be_done_repository:
            save_jtbd_response = await job_to_be_done_repository.save_jtbd(MapToSaveJtbdRequest(record_jtbd_request))
        return MapToRecordJtbdResponse(save_jtbd_response)
