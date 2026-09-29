from __future__ import annotations

import tesser.application as ts

import story_drafting.application.ports as ports
import story_drafting.application.relays as relays
import story_drafting.client as client
import story_drafting.domain as domain


class MapToJobToBeDoneSpec(ts.Mapper, domain.JobToBeDoneSpec):

    def __init__(
        self,
        submit_jtbd_request: client.SubmitJtbdRequest,
        issue_jtbd_id_response: ports.IssueJtbdIdResponse,
    ) -> None:
        super().__init__(
            jtbd_id=issue_jtbd_id_response.jtbd_id,
            statement=submit_jtbd_request.statement,
            step=submit_jtbd_request.step,
            draft_count=submit_jtbd_request.draft_count,
            picked_draft=submit_jtbd_request.picked_draft,
        )


class MapToWorkThroughJtbdRequest(ts.Mapper, relays.WorkThroughJtbdRequest):

    def __init__(self, job_to_be_done: domain.JobToBeDone) -> None:
        super().__init__(
            jtbd_id=str(job_to_be_done.identity),
            statement=str(job_to_be_done.statement),
            step=str(job_to_be_done.step),
            draft_count=int(job_to_be_done.draft_count),
            picked_draft=str(job_to_be_done.picked_draft),
        )


class MapToSubmitJtbdResponse(ts.Mapper, client.SubmitJtbdResponse):

    def __init__(self, work_through_jtbd_response: relays.WorkThroughJtbdResponse) -> None:
        super().__init__(jtbd_id=work_through_jtbd_response.jtbd_id)


class MapToLoadJtbdRequest(ts.Mapper, ports.LoadJtbdRequest):

    def __init__(self, jtbd_id: domain.JtbdId) -> None:
        super().__init__(jtbd_id=str(jtbd_id))


class MapToJobToBeDone(ts.Mapper, client.JobToBeDone):

    def __init__(self, job_to_be_done: ports.JobToBeDone) -> None:
        super().__init__(jtbd_id=job_to_be_done.jtbd_id, statement=job_to_be_done.statement, step=job_to_be_done.step, draft_count=job_to_be_done.draft_count, picked_draft=job_to_be_done.picked_draft)


class MapToComeBackToJtbdResponse(ts.Mapper, client.ComeBackToJtbdResponse):

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
        work_through_jtbd_response = await self._job_to_be_done_orchestrator_relay.run_work_through_jtbd(MapToWorkThroughJtbdRequest(job_to_be_done))
        return MapToSubmitJtbdResponse(work_through_jtbd_response)

    async def come_back_to_jtbd(self, come_back_to_jtbd_request: client.ComeBackToJtbdRequest) -> client.ComeBackToJtbdResponse:
        jtbd_id = domain.JtbdId(come_back_to_jtbd_request.jtbd_id)
        async with self._job_to_be_done_store.transaction() as job_to_be_done_repository:
            load_jtbd_response = await job_to_be_done_repository.load_jtbd(MapToLoadJtbdRequest(jtbd_id))
        return MapToComeBackToJtbdResponse(load_jtbd_response)
