from __future__ import annotations

import tesser.application as ts

import story_drafting.application.ports as ports
import story_drafting.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, record_jtbd_request: relays.RecordJtbdRequest) -> None:
        super().__init__(
            jtbd_id=record_jtbd_request.jtbd_id,
            job=record_jtbd_request.job,
        )


class MapToRecordJtbdResponse(ts.Mapper, relays.RecordJtbdResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(record_jtbd_request))
        return MapToRecordJtbdResponse(save_jtbd_response)
