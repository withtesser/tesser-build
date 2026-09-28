from __future__ import annotations

import drafting.component as component


class TestConfig:

    def test_a_config_carries_its_spec(self) -> None:
        spec = component.Spec(ingress="http://localhost:8080")
        config = component.Config(spec)
        assert config.ingress == spec.ingress


class TestDrafting:

    def test_only_the_workflow_faces_the_ingress_and_each_container_holds_its_handlers(self) -> None:
        drafting = component.Drafting(component.Config(component.Spec(ingress="http://localhost:8080")))
        try:
            declared = [
                (registered.name, registered.ingress_private, sorted(registered.handlers))
                for registered in (drafting.run_actions_service, drafting.run_orchestrator_workflow)
            ]
        finally:
            drafting.close()
        assert declared == [
            ("RunActions", True, ["keep_run"]),
            ("RunOrchestrator", None, ["draft_stories"]),
        ]
