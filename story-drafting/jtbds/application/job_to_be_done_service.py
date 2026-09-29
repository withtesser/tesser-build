from __future__ import annotations

import tesser.application as ts

import jtbds.application.ports as ports
import jtbds.application.relays as relays
import jtbds.client as client
import jtbds.domain as domain


class MapToJobToBeDoneSpec(ts.Mapper, domain.JobToBeDoneSpec):

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

    def __init__(self, job_to_be_done: domain.JobToBeDone) -> None:
        super().__init__(
            jtbd_id=str(job_to_be_done.identity),
            description=str(job_to_be_done.description),
            status=str(job_to_be_done.status),
        )


class MapToSubmitJtbdResponse(ts.Mapper, client.SubmitJtbdResponse):

    def __init__(self, process_jtbd_response: relays.ProcessJtbdResponse) -> None:
        super().__init__(jtbd_id=process_jtbd_response.jtbd_id)


class MapToLoadJtbdRequest(ts.Mapper, ports.LoadJtbdRequest):

    def __init__(self, jtbd_id: domain.JtbdId) -> None:
        super().__init__(jtbd_id=str(jtbd_id))


class MapToJobToBeDone(ts.Mapper, client.JobToBeDone):

    def __init__(self, job_to_be_done: ports.JobToBeDone) -> None:
        super().__init__(jtbd_id=job_to_be_done.jtbd_id, description=job_to_be_done.description, status=job_to_be_done.status)


class MapToCheckJtbdStatusResponse(ts.Mapper, client.CheckJtbdStatusResponse):

    def __init__(self, load_jtbd_response: ports.LoadJtbdResponse) -> None:
        super().__init__(job_to_be_done=MapToJobToBeDone(load_jtbd_response.jtbds[0]))


class JobToBeDoneService(ts.ApplicationService):

    def __init__(
        self,
        job_to_be_done_orchestrator_relay: relays.JobToBeDoneOrchestratorRelay,
        job_to_be_done_identity_repository: ports.JobToBeDoneIdentityRepository,
        job_to_be_done_store: ports.JobToBeDoneStore,
    ) -> None:
        self._job_to_be_done_orchestrator_relay = job_to_be_done_orchestrator_relay
        self._job_to_be_done_identity_repository = job_to_be_done_identity_repository
        self._job_to_be_done_store = job_to_be_done_store

    async def submit_jtbd(self, submit_jtbd_request: client.SubmitJtbdRequest) -> client.SubmitJtbdResponse:
        issue_jtbd_id_response = await self._job_to_be_done_identity_repository.issue_jtbd_id(ports.IssueJtbdIdRequest())
        job_to_be_done = domain.JobToBeDone(MapToJobToBeDoneSpec(submit_jtbd_request, issue_jtbd_id_response))
        process_jtbd_response = await self._job_to_be_done_orchestrator_relay.run_process_jtbd(MapToProcessJtbdRequest(job_to_be_done))
        return MapToSubmitJtbdResponse(process_jtbd_response)

    async def check_jtbd_status(self, check_jtbd_status_request: client.CheckJtbdStatusRequest) -> client.CheckJtbdStatusResponse:
        jtbd_id = domain.JtbdId(check_jtbd_status_request.jtbd_id)
        async with self._job_to_be_done_store.transaction() as job_to_be_done_repository:
            load_jtbd_response = await job_to_be_done_repository.load_jtbd(MapToLoadJtbdRequest(jtbd_id))
        return MapToCheckJtbdStatusResponse(load_jtbd_response)
