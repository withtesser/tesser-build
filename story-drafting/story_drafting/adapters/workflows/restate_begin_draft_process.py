from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import story_drafting.adapters.activities as activities
import story_drafting.application.orchestrators as orchestrators
import story_drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_KEY: typing.Final[str] = "a request names the jtbd its workflow is keyed by"


class RestateBeginDraftProcessRequestSerde(ts.Serde, restate_serde.Serde[relays.BeginDraftProcessRequest]):

    def serialize(self, begin_draft_process_request: relays.BeginDraftProcessRequest | None) -> bytes:
        if begin_draft_process_request is None:
            return b""
        return relays.BeginDraftProcessRequestSnapshot().serialize(begin_draft_process_request)

    def deserialize(self, buf: bytes) -> relays.BeginDraftProcessRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.BeginDraftProcessRequestSnapshot().deserialize(buf)


class RestateBeginDraftProcessResponseSerde(ts.Serde, restate_serde.Serde[relays.BeginDraftProcessResponse]):

    def serialize(self, begin_draft_process_response: relays.BeginDraftProcessResponse | None) -> bytes:
        if begin_draft_process_response is None:
            return b""
        return relays.BeginDraftProcessResponseSnapshot().serialize(begin_draft_process_response)

    def deserialize(self, buf: bytes) -> relays.BeginDraftProcessResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.BeginDraftProcessResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_begin_drafting: activities.RestateBeginDrafting
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_begin_drafting = restate_begin_drafting

    async def run_begin_drafting(self, begin_drafting_request: relays.BeginDraftingRequest) -> relays.BeginDraftingResponse:
        return await self._restate_workflow_context.service_call(self._restate_begin_drafting.handler, begin_drafting_request)


class RestateBeginDraftProcess(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_begin_drafting: activities.RestateBeginDrafting
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateBeginDraftProcessRequestSerde(),
            output_serde=RestateBeginDraftProcessResponseSerde(),
        )
        async def begin_draft_process(
            restate_workflow_context: restate.WorkflowContext, begin_draft_process_request: relays.BeginDraftProcessRequest
        ) -> relays.BeginDraftProcessResponse:
            if begin_draft_process_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_begin_drafting)
            ).begin_draft_process(begin_draft_process_request)

        self.handler = begin_draft_process
