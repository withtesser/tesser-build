from __future__ import annotations

import contextlib
import typing

import tesser.testing as ts

import story_drafting.application as application
import story_drafting.application.ports as ports
import story_drafting.application.relays as relays


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


class TestJobToBeDoneActions:

    async def test_record_jtbd_saves_the_job_to_be_done_under_its_jtbd_id(self) -> None:
        fake_job_to_be_done_store = FakeJobToBeDoneStore()
        job_to_be_done_actions = application.JobToBeDoneActions(fake_job_to_be_done_store)

        await job_to_be_done_actions.record_jtbd(
            relays.RecordJtbdRequest(jtbd_id="jtbd-1", statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary")
        )

        assert fake_job_to_be_done_store.jtbds["jtbd-1"] == ports.JobToBeDone(
            jtbd_id="jtbd-1", statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary"
        )

    async def test_record_jtbd_answers_the_jtbd_id_it_saved(self) -> None:
        job_to_be_done_actions = application.JobToBeDoneActions(FakeJobToBeDoneStore())

        record_jtbd_response = await job_to_be_done_actions.record_jtbd(
            relays.RecordJtbdRequest(jtbd_id="jtbd-1", statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary")
        )

        assert record_jtbd_response.jtbd_id == "jtbd-1"
