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


class RestateConductDraftingRequestSerde(ts.Serde, restate_serde.Serde[relays.ConductDraftingRequest]):

    def serialize(self, conduct_drafting_request: relays.ConductDraftingRequest | None) -> bytes:
        if conduct_drafting_request is None:
            return b""
        return relays.ConductDraftingRequestSnapshot().serialize(conduct_drafting_request)

    def deserialize(self, buf: bytes) -> relays.ConductDraftingRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ConductDraftingRequestSnapshot().deserialize(buf)


class RestateConductDraftingResponseSerde(ts.Serde, restate_serde.Serde[relays.ConductDraftingResponse]):

    def serialize(self, conduct_drafting_response: relays.ConductDraftingResponse | None) -> bytes:
        if conduct_drafting_response is None:
            return b""
        return relays.ConductDraftingResponseSnapshot().serialize(conduct_drafting_response)

    def deserialize(self, buf: bytes) -> relays.ConductDraftingResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ConductDraftingResponseSnapshot().deserialize(buf)


class RestateInvocationJtbdActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_initialize_jtbd: activities.RestateInitializeJtbd
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_initialize_jtbd = restate_initialize_jtbd

    async def run_initialize_jtbd(self, initialize_jtbd_request: relays.InitializeJtbdRequest) -> relays.InitializeJtbdResponse:
        return await self._restate_workflow_context.service_call(self._restate_initialize_jtbd.handler, initialize_jtbd_request)


class RestateConductDrafting(ts.Workflow):

    def __init__(
        self, jtbd_orchestrator_workflow: restate.Workflow, restate_initialize_jtbd: activities.RestateInitializeJtbd
    ) -> None:
        @jtbd_orchestrator_workflow.main(
            input_serde=RestateConductDraftingRequestSerde(),
            output_serde=RestateConductDraftingResponseSerde(),
        )
        async def conduct_drafting(
            restate_workflow_context: restate.WorkflowContext, conduct_drafting_request: relays.ConductDraftingRequest
        ) -> relays.ConductDraftingResponse:
            if conduct_drafting_request.jtbd_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.JtbdOrchestrator(
                RestateInvocationJtbdActionsRelay(restate_workflow_context, restate_initialize_jtbd)
            ).conduct_drafting(conduct_drafting_request)

        self.handler = conduct_drafting
