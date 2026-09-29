from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import jtbd.adapters.activities as activities
import jtbd.application.orchestrators as orchestrators
import jtbd.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_KEY: typing.Final[str] = "a request names the jtbd its workflow is keyed by"


class RestateDraftForJtbdRequestSerde(ts.Serde, restate_serde.Serde[relays.DraftForJtbdRequest]):

    def serialize(self, draft_for_jtbd_request: relays.DraftForJtbdRequest | None) -> bytes:
        if draft_for_jtbd_request is None:
            return b""
        return relays.DraftForJtbdRequestSnapshot().serialize(draft_for_jtbd_request)

    def deserialize(self, buf: bytes) -> relays.DraftForJtbdRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftForJtbdRequestSnapshot().deserialize(buf)


class RestateDraftForJtbdResponseSerde(ts.Serde, restate_serde.Serde[relays.DraftForJtbdResponse]):

    def serialize(self, draft_for_jtbd_response: relays.DraftForJtbdResponse | None) -> bytes:
        if draft_for_jtbd_response is None:
            return b""
        return relays.DraftForJtbdResponseSnapshot().serialize(draft_for_jtbd_response)

    def deserialize(self, buf: bytes) -> relays.DraftForJtbdResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftForJtbdResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_mark_jtbd_drafting: activities.RestateMarkJtbdDrafting
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_mark_jtbd_drafting = restate_mark_jtbd_drafting

    async def run_mark_jtbd_drafting(self, mark_jtbd_drafting_request: relays.MarkJtbdDraftingRequest) -> relays.MarkJtbdDraftingResponse:
        return await self._restate_workflow_context.service_call(self._restate_mark_jtbd_drafting.handler, mark_jtbd_drafting_request)


class RestateDraftForJtbd(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_mark_jtbd_drafting: activities.RestateMarkJtbdDrafting
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateDraftForJtbdRequestSerde(),
            output_serde=RestateDraftForJtbdResponseSerde(),
        )
        async def draft_for_jtbd(
            restate_workflow_context: restate.WorkflowContext, draft_for_jtbd_request: relays.DraftForJtbdRequest
        ) -> relays.DraftForJtbdResponse:
            if draft_for_jtbd_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_mark_jtbd_drafting)
            ).draft_for_jtbd(draft_for_jtbd_request)

        self.handler = draft_for_jtbd
