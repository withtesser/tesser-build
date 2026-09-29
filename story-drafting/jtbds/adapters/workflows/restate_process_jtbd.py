from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import jtbds.adapters.activities as activities
import jtbds.application.orchestrators as orchestrators
import jtbds.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_KEY: typing.Final[str] = "a request names the job_to_be_done its workflow is keyed by"


class RestateProcessJtbdRequestSerde(ts.Serde, restate_serde.Serde[relays.ProcessJtbdRequest]):

    def serialize(self, process_jtbd_request: relays.ProcessJtbdRequest | None) -> bytes:
        if process_jtbd_request is None:
            return b""
        return relays.ProcessJtbdRequestSnapshot().serialize(process_jtbd_request)

    def deserialize(self, buf: bytes) -> relays.ProcessJtbdRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ProcessJtbdRequestSnapshot().deserialize(buf)


class RestateProcessJtbdResponseSerde(ts.Serde, restate_serde.Serde[relays.ProcessJtbdResponse]):

    def serialize(self, process_jtbd_response: relays.ProcessJtbdResponse | None) -> bytes:
        if process_jtbd_response is None:
            return b""
        return relays.ProcessJtbdResponseSnapshot().serialize(process_jtbd_response)

    def deserialize(self, buf: bytes) -> relays.ProcessJtbdResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ProcessJtbdResponseSnapshot().deserialize(buf)


class RestateInvocationJobToBeDoneActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_initialize_jtbd: activities.RestateInitializeJtbd
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_initialize_jtbd = restate_initialize_jtbd

    async def run_initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        return await self._restate_workflow_context.service_call(self._restate_initialize_jtbd.handler, initialize_jtbd_request)


class RestateProcessJtbd(ts.Workflow):

    def __init__(
        self, job_to_be_done_orchestrator_workflow: restate.Workflow, restate_initialize_jtbd: activities.RestateInitializeJtbd
    ) -> None:
        @job_to_be_done_orchestrator_workflow.main(
            input_serde=RestateProcessJtbdRequestSerde(),
            output_serde=RestateProcessJtbdResponseSerde(),
        )
        async def process_jtbd(
            restate_workflow_context: restate.WorkflowContext, process_jtbd_request: relays.ProcessJtbdRequest
        ) -> relays.ProcessJtbdResponse:
            if process_jtbd_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JobToBeDoneOrchestrator(
                RestateInvocationJobToBeDoneActionsRelay(restate_workflow_context, restate_initialize_jtbd)
            ).process_jtbd(process_jtbd_request)

        self.handler = process_jtbd
