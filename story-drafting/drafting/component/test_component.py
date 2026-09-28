from __future__ import annotations

import pytest

import drafting.component as component
import tesser.errors as errors


class TestConfig:

    def test_a_config_carries_its_spec(self) -> None:
        spec = component.Spec(ingress="http://localhost:8080", drafter="anthropic", anthropic_api_key="a key")
        config = component.Config(spec)
        assert (config.ingress, config.drafter, config.anthropic_api_key) == (
            spec.ingress,
            spec.drafter,
            spec.anthropic_api_key,
        )


class TestDrafting:

    def test_only_the_workflow_faces_the_ingress_and_each_container_holds_its_handlers(self) -> None:
        drafting = component.Drafting(
            component.Config(component.Spec(ingress="http://localhost:8080", drafter="canned", anthropic_api_key=""))
        )
        try:
            declared = [
                (registered.name, registered.ingress_private, sorted(registered.handlers))
                for registered in (
                    drafting.run_actions_service,
                    drafting.drafter_actions_service,
                    drafting.run_orchestrator_workflow,
                )
            ]
        finally:
            drafting.close()
        assert declared == [
            ("RunActions", True, ["keep_run", "offer_stories"]),
            ("DrafterActions", True, ["write_stories"]),
            ("RunOrchestrator", None, ["draft_stories"]),
        ]

    def test_the_anthropic_drafter_builds_with_a_key(self) -> None:
        drafting = component.Drafting(
            component.Config(
                component.Spec(ingress="http://localhost:8080", drafter="anthropic", anthropic_api_key="a key")
            )
        )
        try:
            declared = sorted(drafting.drafter_actions_service.handlers)
        finally:
            drafting.close()
        assert declared == ["write_stories"]

    def test_the_anthropic_drafter_without_a_key_fails_at_construction(self) -> None:
        with pytest.raises(errors.DomainError) as refused:
            component.Drafting(
                component.Config(component.Spec(ingress="http://localhost:8080", drafter="anthropic", anthropic_api_key=""))
            )
        assert refused.value.code == "missing_api_key"

    def test_an_absent_or_unknown_drafter_fails_at_construction(self) -> None:
        with pytest.raises(errors.DomainError) as absent:
            component.Drafting(
                component.Config(component.Spec(ingress="http://localhost:8080", drafter="", anthropic_api_key=""))
            )
        with pytest.raises(errors.DomainError) as unknown:
            component.Drafting(
                component.Config(component.Spec(ingress="http://localhost:8080", drafter="gpt", anthropic_api_key=""))
            )
        assert (absent.value.code, unknown.value.code) == ("unknown_drafter", "unknown_drafter")
