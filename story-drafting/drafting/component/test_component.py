from __future__ import annotations

import tempfile

import pytest

import tesser.testing as ts

import drafting.client as client
import drafting.component as component
import tesser.errors as errors


@ts.helper
def spec(
    storage: str = "/tmp/runs",
    ingress: str = "http://127.0.0.1:9",
    drafter: str = "deterministic",
    anthropic_api_key: str = "",
) -> component.Spec:
    return component.Spec(storage=storage, ingress=ingress, drafter=drafter, anthropic_api_key=anthropic_api_key)


class TestConfig:

    def test_a_config_carries_its_spec(self) -> None:
        config = component.Config(spec(drafter="anthropic", anthropic_api_key="key"))

        assert (config.storage, config.ingress, config.drafter, config.anthropic_api_key) == (
            "/tmp/runs",
            "http://127.0.0.1:9",
            "anthropic",
            "key",
        )


class TestDrafting:

    def test_the_workflow_faces_the_ingress_and_the_actions_do_not(self) -> None:
        drafting = component.Drafting(component.Config(spec()))

        assert [
            (registered.name, registered.ingress_private, sorted(registered.handlers))
            for registered in (
                drafting.run_orchestrator_workflow,
                drafting.drafting_actions_service,
                drafting.run_actions_service,
            )
        ] == [
            ("RunOrchestrator", None, ["conduct_run"]),
            ("DraftingActions", True, ["draft_stories"]),
            ("RunActions", True, ["record_run"]),
        ]

    def test_the_anthropic_drafter_is_built_with_its_key(self) -> None:
        drafting = component.Drafting(component.Config(spec(drafter=component.ANTHROPIC, anthropic_api_key="key")))

        assert sorted(drafting.drafting_actions_service.handlers) == ["draft_stories"]

    def test_the_anthropic_drafter_without_a_key_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(spec(drafter=component.ANTHROPIC)))

    def test_an_unknown_drafter_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(spec(drafter="oracle")))

    def test_an_absent_drafter_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(spec(drafter="")))

    async def test_the_wired_client_reads_back_no_run_it_never_opened(self) -> None:
        with tempfile.TemporaryDirectory() as storage:
            drafting = component.Drafting(component.Config(spec(storage=storage)))
            with pytest.raises(client.RunNotFound):
                await drafting.client.get_run(client.GetRunRequest(run_id="never"))
