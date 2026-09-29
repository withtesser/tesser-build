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
            job=submit_jtbd_request.job,
            step=submit_jtbd_request.step,
            draft_count=submit_jtbd_request.draft_count,
            picked_draft=submit_jtbd_request.picked_draft,
        )


class MapToWorkThroughJtbdRequest(ts.Mapper, relays.WorkThroughJtbdRequest):

    def __init__(self, jtbd: domain.Jtbd) -> None:
        super().__init__(
            jtbd_id=str(jtbd.identity),
            job=str(jtbd.job),
            step=str(jtbd.step),
            draft_count=int(jtbd.draft_count),
            picked_draft=str(jtbd.picked_draft),
        )


class MapToSubmitJtbdResponse(ts.Mapper, client.SubmitJtbdResponse):

    def __init__(self, start_work_through_jtbd_response: relays.StartWorkThroughJtbdResponse) -> None:
        super().__init__(jtbd_id=start_work_through_jtbd_response.jtbd_id)


class MapToLoadJtbdRequest(ts.Mapper, ports.LoadJtbdRequest):

    def __init__(self, jtbd_id: domain.JtbdId) -> None:
        super().__init__(jtbd_id=str(jtbd_id))


class MapToJtbd(ts.Mapper, client.Jtbd):

    def __init__(self, jtbd: ports.Jtbd) -> None:
        super().__init__(jtbd_id=jtbd.jtbd_id, job=jtbd.job, step=jtbd.step, draft_count=jtbd.draft_count, picked_draft=jtbd.picked_draft)


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
        start_work_through_jtbd_response = await self._jtbd_orchestrator_relay.start_work_through_jtbd(
            MapToWorkThroughJtbdRequest(jtbd)
        )
        return MapToSubmitJtbdResponse(start_work_through_jtbd_response)

    async def get_jtbd(self, get_jtbd_request: client.GetJtbdRequest) -> client.GetJtbdResponse:
        jtbd_id = domain.JtbdId(get_jtbd_request.jtbd_id)
        async with self._jtbd_store.transaction() as jtbd_repository:
            load_jtbd_response = await jtbd_repository.load_jtbd(MapToLoadJtbdRequest(jtbd_id))
        return MapToGetJtbdResponse(load_jtbd_response)
