from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.adapters.activities as activities
import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_RUN: typing.Final[str] = "a run names the run id its workflow is keyed by"


class RestateDraftStoriesRequestSerde(ts.Serde, restate_serde.Serde[relays.DraftStoriesRequest]):

    def serialize(self, draft_stories_request: relays.DraftStoriesRequest | None) -> bytes:
        if draft_stories_request is None:
            return b""
        return relays.DraftStoriesRequestSnapshot().serialize(draft_stories_request)

    def deserialize(self, buf: bytes) -> relays.DraftStoriesRequest | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftStoriesRequestSnapshot().deserialize(buf)


class RestateDraftStoriesResponseSerde(ts.Serde, restate_serde.Serde[relays.DraftStoriesResponse]):

    def serialize(self, draft_stories_response: relays.DraftStoriesResponse | None) -> bytes:
        if draft_stories_response is None:
            return b""
        return relays.DraftStoriesResponseSnapshot().serialize(draft_stories_response)

    def deserialize(self, buf: bytes) -> relays.DraftStoriesResponse | None:
        if not buf:
            raise restate.TerminalError(_EMPTY_BODY, status_code=400)
        return relays.DraftStoriesResponseSnapshot().deserialize(buf)


class RestateInvocationRunActionsRelay(ts.Dispatcher):

    def __init__(self, restate_workflow_context: restate.WorkflowContext, restate_keep_run: activities.RestateKeepRun) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_keep_run = restate_keep_run

    async def run_keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
        return await self._restate_workflow_context.service_call(self._restate_keep_run.handler, keep_run_request)


class RestateDraftStories(ts.Workflow):

    def __init__(self, run_orchestrator_workflow: restate.Workflow, restate_keep_run: activities.RestateKeepRun) -> None:
        @run_orchestrator_workflow.main(
            input_serde=RestateDraftStoriesRequestSerde(),
            output_serde=RestateDraftStoriesResponseSerde(),
        )
        async def draft_stories(
            restate_workflow_context: restate.WorkflowContext, draft_stories_request: relays.DraftStoriesRequest
        ) -> relays.DraftStoriesResponse:
            if str(draft_stories_request.run_id) != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_RUN, status_code=400)
            return await orchestrators.RunOrchestrator(
                RestateInvocationRunActionsRelay(restate_workflow_context, restate_keep_run),
            ).draft_stories(draft_stories_request)

        self.handler = draft_stories
