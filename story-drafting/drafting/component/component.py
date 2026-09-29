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

    def __init__(self, ingress: str, identity_seed: int) -> None:
        self.ingress = ingress
        self.identity_seed = identity_seed


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.identity_seed = spec.identity_seed


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        self._memory_jtbd_store = repositories.MemoryJtbdStore()
        self.jtbd_actions_service: restate.Service = restate.Service(
            "JtbdActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.jtbd_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "JtbdOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_begin_drafting = workflows.RestateBeginDrafting(
            self.jtbd_orchestrator_workflow,
            activities.RestateRecordJtbd(
                self.jtbd_actions_service, application.JtbdActions(self._memory_jtbd_store)
            ),
        )
        self.client: client.DraftingClient = application.JtbdService(
            dispatchers.RestateHttpJtbdOrchestratorRelay(config.ingress, restate_begin_drafting),
            repositories.UuidJtbdIdentityRepository(config.identity_seed),
            self._memory_jtbd_store,
        )

    async def close(self) -> None:
        return None
