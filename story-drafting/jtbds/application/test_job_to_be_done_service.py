from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import jtbds.application as application
import jtbds.application.ports as ports
import jtbds.application.relays as relays
import jtbds.client as client


@ts.fake
class FakeJobToBeDoneOrchestratorRelay(relays.JobToBeDoneOrchestratorRelay):

    def __init__(self) -> None:
        self.conducted: list[relays.ProcessJtbdRequest] = []

    async def run_process_jtbd(self, process_jtbd_request: relays.ProcessJtbdRequest) -> relays.ProcessJtbdResponse:
        self.conducted.append(process_jtbd_request)
        return relays.ProcessJtbdResponse(jtbd_id=process_jtbd_request.jtbd_id)


@ts.fake
class FakeJobToBeDoneIdentityRepository(ports.JobToBeDoneIdentityRepository):

    async def issue_jtbd_id(self, issue_jtbd_id_request: ports.IssueJtbdIdRequest) -> ports.IssueJtbdIdResponse:
        return ports.IssueJtbdIdResponse(jtbd_id="jtbd-2")


@ts.fake
class FakeJobToBeDoneRepository(ports.JobToBeDoneRepository):

    def __init__(self, jtbds: dict[str, ports.JobToBeDone]) -> None:
        self._jtbds = jtbds

    async def save_jtbd(self, save_jtbd_request: ports.SaveJtbdRequest) -> ports.SaveJtbdResponse:
        self._jtbds[save_jtbd_request.jtbd_id] = ports.JobToBeDone(
            jtbd_id=save_jtbd_request.jtbd_id,
            description=save_jtbd_request.description,
            status=save_jtbd_request.status,
        )
        return ports.SaveJtbdResponse(jtbd_id=save_jtbd_request.jtbd_id)

    async def load_jtbd(self, load_jtbd_request: ports.LoadJtbdRequest) -> ports.LoadJtbdResponse:
        return ports.LoadJtbdResponse(jtbds=(self._jtbds[load_jtbd_request.jtbd_id],))


@ts.fake
class FakeJobToBeDoneStore(ports.JobToBeDoneStore):

    def __init__(self) -> None:
        self.jtbds: dict[str, ports.JobToBeDone] = {}

    @contextlib.asynccontextmanager
    async def transaction(self) -> typing.AsyncIterator[ports.JobToBeDoneRepository]:
        yield FakeJobToBeDoneRepository(self.jtbds)


class TestJobToBeDoneService:

    async def test_submit_jtbd_conducts_the_job_to_be_done_under_the_jtbd_id_its_identity_repository_issued(self) -> None:
        fake_job_to_be_done_orchestrator_relay = FakeJobToBeDoneOrchestratorRelay()
        job_to_be_done_service = application.JobToBeDoneService(
            fake_job_to_be_done_orchestrator_relay, FakeJobToBeDoneIdentityRepository(), FakeJobToBeDoneStore()
        )

        submit_jtbd_response = await job_to_be_done_service.submit_jtbd(
            client.SubmitJtbdRequest(description="design new feature", status="drafting")
        )

        assert [
            (conducted.jtbd_id, conducted.description, conducted.status)
            for conducted in fake_job_to_be_done_orchestrator_relay.conducted
        ] == [("jtbd-2", "design new feature", "drafting")]
        assert submit_jtbd_response.jtbd_id == "jtbd-2"

    async def test_a_saved_job_to_be_done_is_read_back_by_its_jtbd_id(self) -> None:
        fake_job_to_be_done_store = FakeJobToBeDoneStore()
        fake_job_to_be_done_store.jtbds["jtbd-1"] = ports.JobToBeDone(
            jtbd_id="jtbd-1", description="design new feature", status="drafting"
        )
        job_to_be_done_service = application.JobToBeDoneService(
            FakeJobToBeDoneOrchestratorRelay(), FakeJobToBeDoneIdentityRepository(), fake_job_to_be_done_store
        )

        check_jtbd_status_response = await job_to_be_done_service.check_jtbd_status(client.CheckJtbdStatusRequest(jtbd_id="jtbd-1"))

        assert check_jtbd_status_response.job_to_be_done.jtbd_id == "jtbd-1"
        assert check_jtbd_status_response.job_to_be_done.description == "design new feature"
        assert check_jtbd_status_response.job_to_be_done.status == "drafting"
