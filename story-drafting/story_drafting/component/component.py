from __future__ import annotations

import typing

import tesser.component as ts
import restate

import story_drafting.adapters.activities as activities
import story_drafting.adapters.dispatchers as dispatchers
import story_drafting.adapters.repositories as repositories
import story_drafting.adapters.workflows as workflows
import story_drafting.application as application
import story_drafting.client as client

_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(self, ingress: str, identity_seed: int) -> None:
        self.ingress = ingress
        self.identity_seed = identity_seed


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.identity_seed = spec.identity_seed


class StoryDrafting(ts.Component):

    def __init__(self, config: Config) -> None:
        self._memory_jtbd_store = repositories.MemoryJtbdStore()
        self.jtbd_actions_service: restate.Service = restate.Service(
            "JtbdActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.jtbd_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "JtbdOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_begin_draft_process = workflows.RestateBeginDraftProcess(
            self.jtbd_orchestrator_workflow,
            activities.RestateBeginDrafting(
                self.jtbd_actions_service, application.JtbdActions(self._memory_jtbd_store)
            ),
        )
        self.client: client.StoryDraftingClient = application.JtbdService(
            dispatchers.RestateHttpJtbdOrchestratorRelay(config.ingress, restate_begin_draft_process),
            repositories.UuidJtbdIdentityRepository(config.identity_seed),
            self._memory_jtbd_store,
        )

    async def close(self) -> None:
        return None
