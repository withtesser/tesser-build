from __future__ import annotations

import typing

import tesser.component as ts
import restate

import drafting.adapters.activities as activities
import drafting.adapters.dispatchers as dispatchers
import drafting.adapters.gateways as gateways
import drafting.adapters.repositories as repositories
import drafting.adapters.workflows as workflows
import drafting.application as application
import drafting.client as client
import tesser.errors as errors

_DETERMINISTIC: typing.Final[str] = "deterministic"
_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(self, ingress: str, drafter: str, storage: str) -> None:
        self.ingress = ingress
        self.drafter = drafter
        self.storage = storage


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.drafter = spec.drafter
        self.storage = spec.storage


class Drafting(ts.Component):

    class Client:

        def __init__(self, drafting_service: application.DraftingService) -> None:
            self._drafting_service = drafting_service

        async def draft_stories(
            self, draft_stories_request: client.DraftStoriesRequest
        ) -> client.DraftStoriesResponse:
            return await self._drafting_service.draft_stories(draft_stories_request)

        async def get_drafting(self, get_drafting_request: client.GetDraftingRequest) -> client.GetDraftingResponse:
            return await self._drafting_service.get_drafting(get_drafting_request)

    def __init__(self, config: Config) -> None:
        if config.drafter != _DETERMINISTIC:
            raise errors.invalid("unknown_drafter", f"drafter {config.drafter!r} not supported")
        if not config.storage:
            raise errors.invalid("missing_storage", "drafting storage names a directory")
        self._file_drafting_store = repositories.FileDraftingStore(config.storage)
        self.writing_actions_service: restate.Service = restate.Service(
            "WritingActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.drafting_actions_service: restate.Service = restate.Service(
            "DraftingActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.drafting_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "DraftingOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_conduct_drafting = workflows.RestateConductDrafting(
            self.drafting_orchestrator_workflow,
            activities.RestateWriteStories(
                self.writing_actions_service, application.WritingActions(gateways.DeterministicStoryWriter())
            ),
            activities.RestateKeepDraftedStories(
                self.drafting_actions_service, application.DraftingActions(self._file_drafting_store)
            ),
        )
        self.client: client.DraftingClient = Drafting.Client(
            application.DraftingService(
                self._file_drafting_store,
                dispatchers.RestateHttpDraftingOrchestratorRelay(config.ingress, restate_conduct_drafting),
            )
        )

    async def close(self) -> None:
        return None
