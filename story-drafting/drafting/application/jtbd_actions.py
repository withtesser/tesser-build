from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, record_submission_request: relays.RecordSubmissionRequest) -> None:
        super().__init__(
            jtbd_id=record_submission_request.jtbd_id,
            job=record_submission_request.job,
        )


class MapToRecordSubmissionResponse(ts.Mapper, relays.RecordSubmissionResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def record_submission(self, record_submission_request: relays.RecordSubmissionRequest) -> relays.RecordSubmissionResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(record_submission_request))
        return MapToRecordSubmissionResponse(save_jtbd_response)
