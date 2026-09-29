from __future__ import annotations

import tesser.application as ts

import story_drafting.application.ports as ports
import story_drafting.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> None:
        super().__init__(
            jtbd_id=initialize_jtbd_request.jtbd_id,
            status=initialize_jtbd_request.status,
        )


class MapToInitializeJtbdResponse(ts.Mapper, relays.InitializeJtbdResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(initialize_jtbd_request))
        return MapToInitializeJtbdResponse(save_jtbd_response)
