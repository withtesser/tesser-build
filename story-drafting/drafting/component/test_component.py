from __future__ import annotations

import tempfile

import pytest

import drafting.client as client
import drafting.component as component


class TestConfig:

    def test_a_config_carries_its_spec(self) -> None:
        spec = component.Spec(storage="/tmp/runs", ingress="http://localhost:8080")
        config = component.Config(spec)

        assert (config.storage, config.ingress) == (spec.storage, spec.ingress)


class TestDrafting:

    def test_the_workflow_faces_the_ingress_and_holds_the_run_it_conducts(self) -> None:
        drafting = component.Drafting(
            component.Config(component.Spec(storage="/tmp/runs", ingress="http://localhost:8080"))
        )
        registered = drafting.run_orchestrator_workflow

        assert (registered.name, registered.ingress_private, sorted(registered.handlers)) == (
            "RunOrchestrator",
            None,
            ["conduct_run"],
        )

    async def test_the_wired_client_reads_back_no_run_it_never_opened(self) -> None:
        with tempfile.TemporaryDirectory() as storage:
            drafting = component.Drafting(
                component.Config(component.Spec(storage=storage, ingress="http://127.0.0.1:9"))
            )
            with pytest.raises(client.RunNotFound):
                await drafting.client.get_run(client.GetRunRequest(run_id="never"))
