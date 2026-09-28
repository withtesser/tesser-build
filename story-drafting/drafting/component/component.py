from __future__ import annotations

import typing

import tesser.component as ts
import restate

import drafting.adapters.dispatchers as dispatchers
import drafting.adapters.repositories as repositories
import drafting.adapters.workflows as workflows
import drafting.application as application
import drafting.client as client

_RETRY_POLICY: typing.Final[restate.InvocationRetryPolicy] = restate.InvocationRetryPolicy(
    max_attempts=5, on_max_attempts="pause"
)


class Spec(ts.Spec):

    def __init__(self, storage: str, ingress: str) -> None:
        self.storage = storage
        self.ingress = ingress


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.storage = spec.storage
        self.ingress = spec.ingress


class Drafting(ts.Component):

    def __init__(self, config: Config) -> None:
        self._file_run_store = repositories.FileRunStore(config.storage)
        self.run_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "RunOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_conduct_run = workflows.RestateConductRun(self.run_orchestrator_workflow)
        self.client: client.DraftingClient = application.RunService(
            self._file_run_store,
            dispatchers.RestateHttpRunOrchestratorRelay(config.ingress, restate_conduct_run),
        )

    def close(self) -> None:
        return None
