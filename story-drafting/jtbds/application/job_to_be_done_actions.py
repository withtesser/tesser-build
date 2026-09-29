from __future__ import annotations

import tesser.application as ts

import jtbds.application.ports as ports
import jtbds.application.relays as relays


class MapToSaveJtbdRequest(ts.Mapper, ports.SaveJtbdRequest):

    def __init__(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> None:
        super().__init__(
            jtbd_id=initialize_jtbd_request.jtbd_id,
            description=initialize_jtbd_request.description,
            status=initialize_jtbd_request.status,
        )


class MapToInitializeJtbdResponse(ts.Mapper, relays.InitializeJtbdResponse):

    def __init__(self, save_jtbd_response: ports.SaveJtbdResponse) -> None:
        super().__init__(jtbd_id=save_jtbd_response.jtbd_id)


class JobToBeDoneActions(ts.Actions):

    def __init__(self, job_to_be_done_store: ports.JobToBeDoneStore) -> None:
        self._job_to_be_done_store = job_to_be_done_store

    async def initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        async with self._job_to_be_done_store.transaction() as job_to_be_done_repository:
            save_jtbd_response = await job_to_be_done_repository.save_jtbd(MapToSaveJtbdRequest(initialize_jtbd_request))
        return MapToInitializeJtbdResponse(save_jtbd_response)
