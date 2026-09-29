from __future__ import annotations

import tesser.application as ts

import jtbds.application.ports as ports
import jtbds.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, draft_jtbd_request: relays.DraftJtbdRequest) -> None:
        super().__init__(
            jtbd_id=draft_jtbd_request.jtbd_id,
            description=draft_jtbd_request.description,
            status=draft_jtbd_request.status,
        )


class MapToDraftJtbdResponse(ts.Mapper, relays.DraftJtbdResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def draft_jtbd(self, draft_jtbd_request: relays.DraftJtbdRequest) -> relays.DraftJtbdResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(draft_jtbd_request))
        return MapToDraftJtbdResponse(save_jtbd_response)
