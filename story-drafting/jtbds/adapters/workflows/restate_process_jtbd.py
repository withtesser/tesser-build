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


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_draft_jtbd: activities.RestateDraftJtbd
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_draft_jtbd = restate_draft_jtbd

    async def run_draft_jtbd(self, draft_jtbd_request: relays.DraftJtbdRequest) -> relays.DraftJtbdResponse:
        return await self._restate_workflow_context.service_call(self._restate_draft_jtbd.handler, draft_jtbd_request)


class RestateProcessJtbd(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_draft_jtbd: activities.RestateDraftJtbd
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateProcessJtbdRequestSerde(),
            output_serde=RestateProcessJtbdResponseSerde(),
        )
        async def process_jtbd(
            restate_workflow_context: restate.WorkflowContext, process_jtbd_request: relays.ProcessJtbdRequest
        ) -> relays.ProcessJtbdResponse:
            if process_jtbd_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_draft_jtbd)
            ).process_jtbd(process_jtbd_request)

        self.handler = process_jtbd
