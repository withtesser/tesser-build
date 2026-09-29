from __future__ import annotations

import typing

import tesser.component as ts
import restate

import jtbds.adapters.activities as activities
import jtbds.adapters.dispatchers as dispatchers
import jtbds.adapters.repositories as repositories
import jtbds.adapters.workflows as workflows
import jtbds.application as application
import jtbds.client as client

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


class Jtbds(ts.Component):

    def __init__(self, config: Config) -> None:
        self._memory_job_to_be_done_store = repositories.MemoryJobToBeDoneStore()
        self.job_to_be_done_actions_service: restate.Service = restate.Service(
            "JobToBeDoneActions", ingress_private=True, invocation_retry_policy=_RETRY_POLICY
        )
        self.job_to_be_done_orchestrator_workflow: restate.Workflow = restate.Workflow(
            "JobToBeDoneOrchestrator", invocation_retry_policy=_RETRY_POLICY
        )
        restate_process_jtbd = workflows.RestateProcessJtbd(
            self.job_to_be_done_orchestrator_workflow,
            activities.RestateInitializeJtbd(
                self.job_to_be_done_actions_service, application.JobToBeDoneActions(self._memory_job_to_be_done_store)
            ),
        )
        self.client: client.JtbdsClient = application.JobToBeDoneService(
            dispatchers.RestateHttpJobToBeDoneOrchestratorRelay(config.ingress, restate_process_jtbd),
            repositories.UuidJobToBeDoneIdentityRepository(config.identity_seed),
            self._memory_job_to_be_done_store,
        )

    async def close(self) -> None:
        return None
