from __future__ import annotations

import tesser.application as ts

import story_drafting.application.ports as ports
import story_drafting.application.relays as relays
import story_drafting.client as client
import story_drafting.domain as domain


class MapToJtbdSpec(ts.Mapper, domain.JtbdSpec):

    def __init__(
        self,
        submit_jtbd_request: client.SubmitJtbdRequest,
        issue_jtbd_id_response: ports.IssueJtbdIdResponse,
    ) -> None:
        super().__init__(
            jtbd_id=issue_jtbd_id_response.jtbd_id,
            job=submit_jtbd_request.job,
        )


class MapToWorkThroughJtbdRequest(ts.Mapper, relays.WorkThroughJtbdRequest):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.identity),
            job=str(jtbd.job),
        )


class MapToSubmitJtbdResponse(ts.Mapper, client.SubmitJtbdResponse):

    def __init__(self, work_through_jtbd_response: relays.WorkThroughJtbdResponse) -> None:
        super().__init__(jtbd_id=work_through_jtbd_response.jtbd_id)


class MapToLoadJtbdRequest(ts.Mapper, ports.LoadJtbdRequest):

    def __init__(self, jtbd_id: domain.JtbdId) -> None:
        super().__init__(jtbd_id=str(jtbd_id))


class MapToJtbd(ts.Mapper, client.Jtbd):

    def __init__(self, jtbd: ports.Jtbd) -> None:
        super().__init__(jtbd_id=jtbd.jtbd_id, job=jtbd.job)


class MapToComeBackToJtbdResponse(ts.Mapper, client.ComeBackToJtbdResponse):

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

    async def come_back_to_jtbd(self, come_back_to_jtbd_request: client.ComeBackToJtbdRequest) -> client.ComeBackToJtbdResponse:
        jtbd_id = domain.JtbdId(come_back_to_jtbd_request.jtbd_id)
        async with self._jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(MapToLoadJtbdRequest(jtbd_id))
        return MapToComeBackToJtbdResponse(load_jtbd_response)
