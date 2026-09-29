from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import story_drafting.application as application
import story_drafting.application.ports as ports
import story_drafting.application.relays as relays
import story_drafting.client as client


@ts.fake
class FakeJobToBeDoneOrchestratorRelay(relays.JobToBeDoneOrchestratorRelay):

    def __init__(self) -> None:
        self.conducted: list[relays.WorkThroughJtbdRequest] = []

    async def run_work_through_jtbd(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> relays.WorkThroughJtbdResponse:
        self.conducted.append(work_through_jtbd_request)
        return relays.WorkThroughJtbdResponse(jtbd_id=work_through_jtbd_request.jtbd_id)


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
            statement=save_jtbd_request.statement,
            step=save_jtbd_request.step,
            draft_count=save_jtbd_request.draft_count,
            picked_draft=save_jtbd_request.picked_draft,
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
            client.SubmitJtbdRequest(statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary")
        )

        assert [
            (conducted.jtbd_id, conducted.statement, conducted.step, conducted.draft_count, conducted.picked_draft)
            for conducted in fake_job_to_be_done_orchestrator_relay.conducted
        ] == [("jtbd-2", "When I plan a trip I want an itinerary", "drafting", 1, "As a traveller I want an itinerary")]
        assert submit_jtbd_response.jtbd_id == "jtbd-2"

    async def test_a_saved_job_to_be_done_is_read_back_by_its_jtbd_id(self) -> None:
        fake_job_to_be_done_store = FakeJobToBeDoneStore()
        fake_job_to_be_done_store.jtbds["jtbd-1"] = ports.JobToBeDone(
            jtbd_id="jtbd-1", statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary"
        )
        job_to_be_done_service = application.JobToBeDoneService(
            FakeJobToBeDoneOrchestratorRelay(), FakeJobToBeDoneIdentityRepository(), fake_job_to_be_done_store
        )

        come_back_to_jtbd_response = await job_to_be_done_service.come_back_to_jtbd(client.ComeBackToJtbdRequest(jtbd_id="jtbd-1"))

        assert come_back_to_jtbd_response.job_to_be_done.jtbd_id == "jtbd-1"
        assert come_back_to_jtbd_response.job_to_be_done.statement == "When I plan a trip I want an itinerary"
        assert come_back_to_jtbd_response.job_to_be_done.step == "drafting"
        assert come_back_to_jtbd_response.job_to_be_done.draft_count == 1
        assert come_back_to_jtbd_response.job_to_be_done.picked_draft == "As a traveller I want an itinerary"
