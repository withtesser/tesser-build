from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.client as client
import drafting.domain as domain


class MapToJtbdSpec(ts.Mapper, domain.JtbdSpec):

    def __init__(
        self,
        submit_jtbd_request: client.SubmitJtbdRequest,
        issue_jtbd_id_response: ports.IssueJtbdIdResponse,
    ) -> None:
        super().__init__(
            jtbd_id=issue_jtbd_id_response.jtbd_id,
            situation=submit_jtbd_request.situation,
            motivation=submit_jtbd_request.motivation,
            outcome=submit_jtbd_request.outcome,
        )


class MapToWorkThroughJtbdRequest(ts.Mapper, relays.WorkThroughJtbdRequest):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.identity),
            situation=str(jtbd.situation),
            motivation=str(jtbd.motivation),
            outcome=str(jtbd.outcome),
        )


class MapToSubmitJtbdResponse(ts.Mapper, client.SubmitJtbdResponse):

    def __init__(self, work_through_jtbd_response: relays.WorkThroughJtbdResponse) -> None:
        super().__init__(jtbd_id=work_through_jtbd_response.jtbd_id)


class MapToLoadJtbdRequest(ts.Mapper, ports.LoadJtbdRequest):

    def __init__(self, jtbd_id: domain.JtbdId) -> None:
        super().__init__(jtbd_id=str(jtbd_id))


class MapToJtbd(ts.Mapper, client.Jtbd):

    def __init__(self, jtbd: ports.Jtbd) -> None:
        super().__init__(jtbd_id=jtbd.jtbd_id, situation=jtbd.situation, motivation=jtbd.motivation, outcome=jtbd.outcome)


class MapToGetJtbdResponse(ts.Mapper, client.GetJtbdResponse):

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
        work_through_jtbd_response = await self._jtbd_orchestrator_relay.run_work_through_jtbd(MapToWorkThroughJtbdRequest(jtbd))
        return MapToSubmitJtbdResponse(work_through_jtbd_response)

    async def get_jtbd(self, get_jtbd_request: client.GetJtbdRequest) -> client.GetJtbdResponse:
        jtbd_id = domain.JtbdId(get_jtbd_request.jtbd_id)
        async with self._jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(MapToLoadJtbdRequest(jtbd_id))
        return MapToGetJtbdResponse(load_jtbd_response)
