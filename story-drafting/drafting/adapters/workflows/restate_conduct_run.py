from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.adapters.activities as activities
import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_KEY: typing.Final[str] = "a request names the run its workflow is keyed by"


class RestateConductRunRequestSerde(ts.Serde, restate_serde.Serde[relays.ConductRunRequest]):

    def serialize(self, conduct_run_request: relays.ConductRunRequest | None) -> bytes:
        if conduct_run_request is None:
            return b""
        return relays.ConductRunRequestSnapshot().serialize(conduct_run_request)

    def deserialize(self, buf: bytes) -> relays.ConductRunRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ConductRunRequestSnapshot().deserialize(buf)


class RestateConductRunResponseSerde(ts.Serde, restate_serde.Serde[relays.ConductRunResponse]):

    def serialize(self, conduct_run_response: relays.ConductRunResponse | None) -> bytes:
        if conduct_run_response is None:
            return b""
        return relays.ConductRunResponseSnapshot().serialize(conduct_run_response)

    def deserialize(self, buf: bytes) -> relays.ConductRunResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.ConductRunResponseSnapshot().deserialize(buf)


class RestateInvocationRunActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_record_run: activities.RestateRecordRun
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_record_run = restate_record_run

    async def run_record_run(self, record_run_request: relays.RecordRunRequest) -> relays.RecordRunResponse:
        return await self._restate_workflow_context.service_call(self._restate_record_run.handler, record_run_request)


class RestateConductRun(ts.Workflow):

    def __init__(
        self, run_orchestrator_workflow: restate.Workflow, restate_record_run: activities.RestateRecordRun
    ) -> None:
        @run_orchestrator_workflow.main(
            input_serde=RestateConductRunRequestSerde(),
            output_serde=RestateConductRunResponseSerde(),
        )
        async def conduct_run(
            restate_workflow_context: restate.WorkflowContext, conduct_run_request: relays.ConductRunRequest
        ) -> relays.ConductRunResponse:
            if conduct_run_request.run_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_KEY, status_code=400)
            return await orchestrators.RunOrchestrator(
                RestateInvocationRunActionsRelay(restate_workflow_context, restate_record_run)
            ).conduct_run(conduct_run_request)

        self.handler = conduct_run
