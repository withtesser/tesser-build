from __future__ import annotations

import tesser.application as ts

import story_drafting.application.relays as relays


class MapToRecordJtbdRequest(ts.Mapper, relays.RecordJtbdRequest):

    def __init__(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> None:
        super().__init__(
            jtbd_id=work_through_jtbd_request.jtbd_id,
            statement=work_through_jtbd_request.statement,
            step=work_through_jtbd_request.step,
            draft_count=work_through_jtbd_request.draft_count,
            picked_draft=work_through_jtbd_request.picked_draft,
        )


class MapToWorkThroughJtbdResponse(ts.Mapper, relays.WorkThroughJtbdResponse):

    def __init__(self, record_jtbd_response: relays.RecordJtbdResponse) -> None:
        super().__init__(jtbd_id=record_jtbd_response.jtbd_id)


class JobToBeDoneOrchestrator(ts.Orchestrator):

    def __init__(self, job_to_be_done_actions_relay: relays.JobToBeDoneActionsRelay) -> None:
        self._job_to_be_done_actions_relay = job_to_be_done_actions_relay

    async def work_through_jtbd(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> relays.WorkThroughJtbdResponse:
        record_jtbd_response = await self._job_to_be_done_actions_relay.run_record_jtbd(
            MapToRecordJtbdRequest(work_through_jtbd_request)
        )
        return MapToWorkThroughJtbdResponse(record_jtbd_response)
