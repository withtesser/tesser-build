from __future__ import annotations

import tesser.application as ts

import jtbds.application.ports as ports
import jtbds.application.relays as relays
import jtbds.client as client
import jtbds.domain as domain


class MapToJtbdSpec(ts.Mapper, domain.JtbdSpec):

    def __init__(
        self,
        submit_jtbd_request: client.SubmitJtbdRequest,
        issue_jtbd_id_response: ports.IssueJtbdIdResponse,
    ) -> None:
        super().__init__(
            jtbd_id=issue_jtbd_id_response.jtbd_id,
            description=submit_jtbd_request.description,
            status=submit_jtbd_request.status,
        )


class MapToProcessJtbdRequest(ts.Mapper, relays.ProcessJtbdRequest):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.identity),
            description=str(jtbd.description),
            status=str(jtbd.status),
        )


class MapToSubmitJtbdResponse(ts.Mapper, client.SubmitJtbdResponse):

    def __init__(self, process_jtbd_response: relays.ProcessJtbdResponse) -> None:
        super().__init__(jtbd_id=process_jtbd_response.jtbd_id)


class MapToLoadJtbdRequest(ts.Mapper, ports.LoadJtbdRequest):

    def __init__(self, jtbd_id: domain.JtbdId) -> None:
        super().__init__(jtbd_id=str(jtbd_id))


class MapToJtbd(ts.Mapper, client.Jtbd):

    def __init__(self, jtbd: ports.Jtbd) -> None:
        super().__init__(jtbd_id=jtbd.jtbd_id, status=jtbd.status)


class MapToCheckJtbdStatusResponse(ts.Mapper, client.CheckJtbdStatusResponse):

    def __init__(self, load_jtbd_response: ports.LoadJtbdResponse) -> None:
        super().__init__(jtbd=MapToJtbd(load_jtbd_response.jtbds[0]))


class JtbdService(ts.ApplicationService):

    def __init__(
        self,
        jtbd_orchestrator_relay: relays.JtbdOrchestratorRelay,
        jtbd_identity_repository: ports.JtbdIdentityRepository,
        jtbd_store: ports.JtbdStore,
    ) -> None:
        self._jtbd_orchestrator_relay = jtbd_orchestrator_relay
        self._jtbd_identity_repository = jtbd_identity_repository
        self._jtbd_store = jtbd_store

    async def submit_jtbd(self, submit_jtbd_request: client.SubmitJtbdRequest) -> client.SubmitJtbdResponse:
        issue_jtbd_id_response = await self._jtbd_identity_repository.issue_jtbd_id(ports.IssueJtbdIdRequest())
        jtbd = domain.Jtbd(MapToJtbdSpec(submit_jtbd_request, issue_jtbd_id_response))
        process_jtbd_response = await self._jtbd_orchestrator_relay.run_process_jtbd(MapToProcessJtbdRequest(jtbd))
        return MapToSubmitJtbdResponse(process_jtbd_response)

    async def check_jtbd_status(self, check_jtbd_status_request: client.CheckJtbdStatusRequest) -> client.CheckJtbdStatusResponse:
        jtbd_id = domain.JtbdId(check_jtbd_status_request.jtbd_id)
        async with self._jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(MapToLoadJtbdRequest(jtbd_id))
        return MapToCheckJtbdStatusResponse(load_jtbd_response)
