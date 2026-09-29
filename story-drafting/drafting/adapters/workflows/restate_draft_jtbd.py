from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.adapters.activities as activities
import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_KEY: typing.Final[str] = "a request names the jtbd its workflow is keyed by"


class RestateDraftJtbdRequestSerde(ts.Serde, restate_serde.Serde[relays.DraftJtbdRequest]):

    def serialize(self, draft_jtbd_request: relays.DraftJtbdRequest | None) -> bytes:
        if draft_jtbd_request is None:
            return b""
        return relays.DraftJtbdRequestSnapshot().serialize(draft_jtbd_request)

    def deserialize(self, buf: bytes) -> relays.DraftJtbdRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftJtbdRequestSnapshot().deserialize(buf)


class RestateDraftJtbdResponseSerde(ts.Serde, restate_serde.Serde[relays.DraftJtbdResponse]):

    def serialize(self, draft_jtbd_response: relays.DraftJtbdResponse | None) -> bytes:
        if draft_jtbd_response is None:
            return b""
        return relays.DraftJtbdResponseSnapshot().serialize(draft_jtbd_response)

    def deserialize(self, buf: bytes) -> relays.DraftJtbdResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftJtbdResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_record_jtbd: activities.RestateRecordJtbd
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_record_jtbd = restate_record_jtbd

    async def run_record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse:
        return await self._restate_workflow_context.service_call(self._restate_record_jtbd.handler, record_jtbd_request)


class RestateDraftJtbd(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_record_jtbd: activities.RestateRecordJtbd
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateDraftJtbdRequestSerde(),
            output_serde=RestateDraftJtbdResponseSerde(),
        )
        async def draft_jtbd(
            restate_workflow_context: restate.WorkflowContext, draft_jtbd_request: relays.DraftJtbdRequest
        ) -> relays.DraftJtbdResponse:
            if draft_jtbd_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_record_jtbd)
            ).draft_jtbd(draft_jtbd_request)

        self.handler = draft_jtbd
