from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, write_drafts_request: relays.WriteDraftsRequest) -> None:
        super().__init__(
            jtbd_id=write_drafts_request.jtbd_id,
            job=write_drafts_request.job,
        )


class MapToWriteDraftsResponse(ts.Mapper, relays.WriteDraftsResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def write_drafts(self, write_drafts_request: relays.WriteDraftsRequest) -> relays.WriteDraftsResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(write_drafts_request))
        return MapToWriteDraftsResponse(save_jtbd_response)
