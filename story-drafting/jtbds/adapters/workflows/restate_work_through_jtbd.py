from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import jtbds.adapters.activities as activities
import jtbds.application.orchestrators as orchestrators
import jtbds.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_KEY: typing.Final[str] = "a request names the jtbd its workflow is keyed by"


class RestateWorkThroughJtbdRequestSerde(ts.Serde, restate_serde.Serde[relays.WorkThroughJtbdRequest]):

    def serialize(self, work_through_jtbd_request: relays.WorkThroughJtbdRequest | None) -> bytes:
        if work_through_jtbd_request is None:
            return b""
        return relays.WorkThroughJtbdRequestSnapshot().serialize(work_through_jtbd_request)

    def deserialize(self, buf: bytes) -> relays.WorkThroughJtbdRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.WorkThroughJtbdRequestSnapshot().deserialize(buf)


class RestateWorkThroughJtbdResponseSerde(ts.Serde, restate_serde.Serde[relays.WorkThroughJtbdResponse]):

    def serialize(self, work_through_jtbd_response: relays.WorkThroughJtbdResponse | None) -> bytes:
        if work_through_jtbd_response is None:
            return b""
        return relays.WorkThroughJtbdResponseSnapshot().serialize(work_through_jtbd_response)

    def deserialize(self, buf: bytes) -> relays.WorkThroughJtbdResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.WorkThroughJtbdResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_record_submission: activities.RestateRecordSubmission
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_record_submission = restate_record_submission

    async def run_record_submission(self, record_submission_request: relays.RecordSubmissionRequest) -> relays.RecordSubmissionResponse:
        return await self._restate_workflow_context.service_call(self._restate_record_submission.handler, record_submission_request)


class RestateWorkThroughJtbd(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_record_submission: activities.RestateRecordSubmission
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateWorkThroughJtbdRequestSerde(),
            output_serde=RestateWorkThroughJtbdResponseSerde(),
        )
        async def work_through_jtbd(
            restate_workflow_context: restate.WorkflowContext, work_through_jtbd_request: relays.WorkThroughJtbdRequest
        ) -> relays.WorkThroughJtbdResponse:
            if work_through_jtbd_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_record_submission)
            ).work_through_jtbd(work_through_jtbd_request)

        self.handler = work_through_jtbd
