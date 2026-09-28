from __future__ import annotations

import pathlib

import pytest

import tesser.testing as ts

import drafting.client as client
import drafting.component as component
import tesser.errors as errors


@ts.helper
def _spec(
    ingress: str = "http://localhost:8080", drafter: str = "deterministic", storage: str = "/tmp/story-drafting"
) -> component.Spec:
    return component.Spec(ingress=ingress, drafter=drafter, storage=storage)


class TestConfig:

    def test_a_config_carries_the_ingress_the_drafter_and_the_storage(self) -> None:
        spec = _spec(ingress="http://localhost:8080", drafter="deterministic", storage="/tmp/drafts")

        config = component.Config(spec)

        assert (config.ingress, config.drafter, config.storage) == (spec.ingress, spec.drafter, spec.storage)


class TestDrafting:

    def test_only_the_workflow_faces_the_ingress_and_each_container_holds_its_handlers(self) -> None:
        drafting = component.Drafting(component.Config(_spec()))

        declared = [
            (registered.name, registered.ingress_private, sorted(registered.handlers))
            for registered in (
                drafting.writing_actions_service,
                drafting.drafting_actions_service,
                drafting.drafting_orchestrator_workflow,
            )
        ]

        assert declared == [
            ("WritingActions", True, ["write_stories"]),
            ("DraftingActions", True, ["keep_drafted_stories"]),
            ("DraftingOrchestrator", None, ["conduct_drafting"]),
        ]

    async def test_the_wired_client_rejects_a_blank_job_before_anything_starts(self, tmp_path: pathlib.Path) -> None:
        drafting = component.Drafting(component.Config(_spec(ingress="http://ingress.invalid", storage=str(tmp_path))))

        with pytest.raises(client.DraftingRejected):
            await drafting.client.draft_stories(client.DraftStoriesRequest(job=" "))

        assert list(tmp_path.iterdir()) == []

    def test_a_drafter_other_than_the_deterministic_one_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(_spec(drafter="a-model-nobody-configured")))

    def test_an_empty_storage_is_refused(self) -> None:
        with pytest.raises(errors.DomainError):
            component.Drafting(component.Config(_spec(storage="")))
