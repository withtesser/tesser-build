from __future__ import annotations

import tesser.application as ts

import jtbds.application.relays as relays


class MapToRecordSubmissionRequest(ts.Mapper, relays.RecordSubmissionRequest):

    def __init__(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> None:
        super().__init__(
            jtbd_id=work_through_jtbd_request.jtbd_id,
            situation=work_through_jtbd_request.situation,
            motivation=work_through_jtbd_request.motivation,
            outcome=work_through_jtbd_request.outcome,
        )


class MapToWorkThroughJtbdResponse(ts.Mapper, relays.WorkThroughJtbdResponse):

    def __init__(self, record_submission_response: relays.RecordSubmissionResponse) -> None:
        super().__init__(jtbd_id=record_submission_response.jtbd_id)


class JtbdOrchestrator(ts.Orchestrator):

    def __init__(self, jtbd_actions_relay: relays.JtbdActionsRelay) -> None:
        self._jtbd_actions_relay = jtbd_actions_relay

    async def work_through_jtbd(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest) -> relays.WorkThroughJtbdResponse:
        record_submission_response = await self._jtbd_actions_relay.run_record_submission(
            MapToRecordSubmissionRequest(work_through_jtbd_request)
        )
        return MapToWorkThroughJtbdResponse(record_submission_response)
