from __future__ import annotations

import tesser.application as ts

import jtbd.application.ports as ports
import jtbd.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest) -> None:
        super().__init__(
            jtbd_id=mark_jtbd_drafting_request.jtbd_id,
            description=mark_jtbd_drafting_request.description,
            status=mark_jtbd_drafting_request.status,
        )


class MapToMarkJtbdDraftingResponse(ts.Mapper, relays.MarkJtbdDraftingResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JtbdActions(ts.Actions):

    def __init__(self, jtbd_store: ports.JtbdStore) -> None:
        self._jtbd_store = jtbd_store

    async def mark_jtbd_drafting(self, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest) -> relays.MarkJtbdDraftingResponse:
        async with self._jtbd_store.transaction() as jtbd_repository:
            save_jtbd_response = await jtbd_repository.save_jtbd(MapToSaveJtbdRequest(mark_jtbd_drafting_request))
        return MapToMarkJtbdDraftingResponse(save_jtbd_response)
