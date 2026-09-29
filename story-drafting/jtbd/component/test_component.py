from __future__ import annotations

import jtbd.component as component


class TestConfig:

    def test_a_config_carries_the_engine_ingress(self) -> None:
        spec = component.Spec(ingress="http://localhost:8080", identity_seed=7)

        config = component.Config(spec)

        assert config.ingress == spec.ingress

    def test_a_config_carries_the_seed_its_identity_repository_is_built_with(self) -> None:
        spec = component.Spec(ingress="http://localhost:8080", identity_seed=7)

        config = component.Config(spec)

        assert config.identity_seed == spec.identity_seed


class TestJtbd:

    async def test_the_component_publishes_the_engine_containers_it_registered_into(self) -> None:
        config = component.Config(
            component.Spec(ingress="http://localhost:8080", identity_seed=7)
        )

        jtbd = component.Jtbd(config)
        registered = {
            jtbd.jtbd_actions_service.name: sorted(jtbd.jtbd_actions_service.handlers),
            jtbd.jtbd_orchestrator_workflow.name: sorted(
                jtbd.jtbd_orchestrator_workflow.handlers
            ),
        }
        await jtbd.close()

        assert registered == {"JtbdActions": ["mark_jtbd_drafting"], "JtbdOrchestrator": ["draft_for_jtbd"]}

    async def test_every_container_bounds_its_retries_and_only_the_workflow_faces_the_ingress(self) -> None:
        config = component.Config(
            component.Spec(ingress="http://localhost:8080", identity_seed=7)
        )

        jtbd = component.Jtbd(config)
        declared = [
            (
                registered.name,
                registered.ingress_private,
                registered.invocation_retry_policy.max_attempts if registered.invocation_retry_policy else None,
                registered.invocation_retry_policy.on_max_attempts if registered.invocation_retry_policy else None,
            )
            for registered in (jtbd.jtbd_actions_service, jtbd.jtbd_orchestrator_workflow)
        ]
        await jtbd.close()

        assert declared == [
            ("JtbdActions", True, 5, "pause"),
            ("JtbdOrchestrator", None, 5, "pause"),
        ]
