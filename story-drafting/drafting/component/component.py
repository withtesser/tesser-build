from __future__ import annotations

import typing

import tesser.component as ts
import restate

import drafting.adapters.activities as activities
import drafting.adapters.dispatchers as dispatchers
import drafting.adapters.repositories as repositories
import drafting.adapters.workflows as workflows
import drafting.application as application
import drafting.client as client

_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(self, ingress: str) -> None:
        self.ingress = ingress


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        self._memory_run_store = repositories.MemoryRunStore()
        self.run_actions_service: restate.Service = restate.Service(
            "RunActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.run_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "RunOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_draft_stories = workflows.RestateDraftStories(
            self.run_orchestrator_workflow,
            activities.RestateRecordRun(self.run_actions_service, application.RunActions(self._memory_run_store)),
        )
        self.client: client.DraftingClient = application.DraftingService(
            self._memory_run_store,
            dispatchers.RestateHttpRunOrchestratorRelay(config.ingress, restate_draft_stories),
        )

    def close(self) -> None:
        return None
