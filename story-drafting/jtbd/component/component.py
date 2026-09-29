from __future__ import annotations

import typing

import tesser.component as ts
import restate

import jtbd.adapters.activities as activities
import jtbd.adapters.dispatchers as dispatchers
import jtbd.adapters.repositories as repositories
import jtbd.adapters.workflows as workflows
import jtbd.application as application
import jtbd.client as client

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


class Jtbd(ts.Component):

    def __init__(self, config: Config) -> None:
        self._memory_jtbd_store = repositories.MemoryJtbdStore()
        self.jtbd_actions_service: restate.Service = restate.Service(
            "JtbdActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.jtbd_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "JtbdOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_draft_for_jtbd = workflows.RestateDraftForJtbd(
            self.jtbd_orchestrator_workflow,
            activities.RestateMarkJtbdDrafting(
                self.jtbd_actions_service, application.JtbdActions(self._memory_jtbd_store)
            ),
        )
        self.client: client.JtbdClient = application.JtbdService(
            dispatchers.RestateHttpJtbdOrchestratorRelay(config.ingress, restate_draft_for_jtbd),
            repositories.UuidJtbdIdentityRepository(config.identity_seed),
            self._memory_jtbd_store,
        )

    async def close(self) -> None:
        return None
