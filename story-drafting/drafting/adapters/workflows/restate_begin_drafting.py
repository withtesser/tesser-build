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


class RestateBeginDraftingRequestSerde(ts.Serde, restate_serde.Serde[relays.BeginDraftingRequest]):

    def serialize(self, begin_drafting_request: relays.BeginDraftingRequest | None) -> bytes:
        if begin_drafting_request is None:
            return b""
        return relays.BeginDraftingRequestSnapshot().serialize(begin_drafting_request)

    def deserialize(self, buf: bytes) -> relays.BeginDraftingRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.BeginDraftingRequestSnapshot().deserialize(buf)


class RestateBeginDraftingResponseSerde(ts.Serde, restate_serde.Serde[relays.BeginDraftingResponse]):

    def serialize(self, begin_drafting_response: relays.BeginDraftingResponse | None) -> bytes:
        if begin_drafting_response is None:
            return b""
        return relays.BeginDraftingResponseSnapshot().serialize(begin_drafting_response)

    def deserialize(self, buf: bytes) -> relays.BeginDraftingResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.BeginDraftingResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_record_jtbd: activities.RestateRecordJtbd
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_record_jtbd = restate_record_jtbd

    async def run_record_jtbd(self, record_jtbd_request: relays.RecordJtbdRequest) -> relays.RecordJtbdResponse:
        return await self._restate_workflow_context.service_call(self._restate_record_jtbd.handler, record_jtbd_request)


class RestateBeginDrafting(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_record_jtbd: activities.RestateRecordJtbd
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateBeginDraftingRequestSerde(),
            output_serde=RestateBeginDraftingResponseSerde(),
        )
        async def begin_drafting(
            restate_workflow_context: restate.WorkflowContext, begin_drafting_request: relays.BeginDraftingRequest
        ) -> relays.BeginDraftingResponse:
            if begin_drafting_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_record_jtbd)
            ).begin_drafting(begin_drafting_request)

        self.handler = begin_drafting
