from __future__ import annotations

import tesser.application as ts

import story_drafting.application.ports as ports
import story_drafting.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, begin_drafting_request: relays.BeginDraftingRequest) -> None:
        super().__init__(
            jtbd_id=begin_drafting_request.jtbd_id,
            status=begin_drafting_request.status,
        )


class MapToBeginDraftingResponse(ts.Mapper, relays.BeginDraftingResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def begin_drafting(self, begin_drafting_request: relays.BeginDraftingRequest) -> relays.BeginDraftingResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(begin_drafting_request))
        return MapToBeginDraftingResponse(save_jtbd_response)
