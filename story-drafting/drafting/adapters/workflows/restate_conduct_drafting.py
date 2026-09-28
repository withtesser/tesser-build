from __future__ import annotations

import typing

import tesser.adapters as ts
import restate
import restate.serde as restate_serde

import drafting.adapters.activities as activities
import drafting.application.orchestrators as orchestrators
import drafting.application.relays as relays

_EMPTY_BODY: typing.Final[str] = "a message crosses the engine with a body"
_FOREIGN_DRAFTING_ID: typing.Final[str] = "a drafting names the drafting id its workflow is keyed by"


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


class RestateInvocationWritingActionsRelay(ts.Dispatcher):

    def __init__(
        self, restate_workflow_context: restate.WorkflowContext, restate_write_stories: activities.RestateWriteStories
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_write_stories = restate_write_stories

    async def run_write_stories(self, write_stories_request: relays.WriteStoriesRequest) -> relays.WriteStoriesResponse:
        return await self._restate_workflow_context.service_call(self._restate_write_stories.handler, write_stories_request)


class RestateInvocationDraftingActionsRelay(ts.Dispatcher):

    def __init__(
        self,
        restate_workflow_context: restate.WorkflowContext,
        restate_keep_drafted_stories: activities.RestateKeepDraftedStories,
    ) -> None:
        self._restate_workflow_context = restate_workflow_context
        self._restate_keep_drafted_stories = restate_keep_drafted_stories

    async def run_keep_drafted_stories(
        self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest
    ) -> relays.KeepDraftedStoriesResponse:
        return await self._restate_workflow_context.service_call(
            self._restate_keep_drafted_stories.handler, keep_drafted_stories_request
        )


class RestateInvocationDraftingOrchestratorSignalRelay(ts.Dispatcher):

    def __init__(self, restate_workflow_context: restate.WorkflowContext) -> None:
        self._restate_workflow_context = restate_workflow_context

    async def await_pick_story(self, await_pick_story_request: relays.AwaitPickStoryRequest) -> relays.AwaitPickStoryResponse:
        return relays.AwaitPickStoryResponseSnapshot().deserialize(
            await self._restate_workflow_context.promise(relays.PICK_STORY_PROMISE, serde=restate_serde.BytesSerde()).value()
        )


class RestateConductDrafting(ts.Workflow):

    def __init__(
        self,
        drafting_orchestrator_workflow: restate.Workflow,
        restate_write_stories: activities.RestateWriteStories,
        restate_keep_drafted_stories: activities.RestateKeepDraftedStories,
    ) -> None:
        @drafting_orchestrator_workflow.main(
            input_serde=RestateConductDraftingRequestSerde(),
            output_serde=RestateConductDraftingResponseSerde(),
        )
        async def conduct_drafting(
            restate_workflow_context: restate.WorkflowContext, conduct_drafting_request: relays.ConductDraftingRequest
        ) -> relays.ConductDraftingResponse:
            if conduct_drafting_request.drafting_id != restate_workflow_context.key():
                raise restate.TerminalError(_FOREIGN_DRAFTING_ID, status_code=400)
            return await orchestrators.DraftingOrchestrator(
                RestateInvocationWritingActionsRelay(restate_workflow_context, restate_write_stories),
                RestateInvocationDraftingActionsRelay(restate_workflow_context, restate_keep_drafted_stories),
                RestateInvocationDraftingOrchestratorSignalRelay(restate_workflow_context),
            ).conduct_drafting(conduct_drafting_request)

        self.handler = conduct_drafting
