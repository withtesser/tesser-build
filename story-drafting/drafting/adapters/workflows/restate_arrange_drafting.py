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


class RestateArrangeDraftingRequestSerde(ts.Serde, restate_serde.Serde[relays.ArrangeDraftingRequest]):

    def serialize(self, arrange_drafting_request: relays.ArrangeDraftingRequest | None) -> bytes:
        if arrange_drafting_request is None:
            return b""
        return relays.ArrangeDraftingRequestSnapshot().serialize(arrange_drafting_request)

    def deserialize(self, buf: bytes) -> relays.ArrangeDraftingRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ArrangeDraftingRequestSnapshot().deserialize(buf)


class RestateArrangeDraftingResponseSerde(ts.Serde, restate_serde.Serde[relays.ArrangeDraftingResponse]):

    def serialize(self, arrange_drafting_response: relays.ArrangeDraftingResponse | None) -> bytes:
        if arrange_drafting_response is None:
            return b""
        return relays.ArrangeDraftingResponseSnapshot().serialize(arrange_drafting_response)

    def deserialize(self, buf: bytes) -> relays.ArrangeDraftingResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ArrangeDraftingResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_draft_jtbd: activities.RestateDraftJtbd
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_draft_jtbd = restate_draft_jtbd

    async def run_draft_jtbd(self, draft_jtbd_request: relays.DraftJtbdRequest) -> relays.DraftJtbdResponse:
        return await self._restate_workflow_context.service_call(self._restate_draft_jtbd.handler, draft_jtbd_request)


class RestateArrangeDrafting(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_draft_jtbd: activities.RestateDraftJtbd
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateArrangeDraftingRequestSerde(),
            output_serde=RestateArrangeDraftingResponseSerde(),
        )
        async def arrange_drafting(
            restate_workflow_context: restate.WorkflowContext, arrange_drafting_request: relays.ArrangeDraftingRequest
        ) -> relays.ArrangeDraftingResponse:
            if arrange_drafting_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_draft_jtbd)
            ).arrange_drafting(arrange_drafting_request)

        self.handler = arrange_drafting
