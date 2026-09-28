from __future__ import annotations

import tesser.testing as ts

import drafting.component as component


@ts.helper
def _spec(ingress: str = "http://localhost:8080", drafter: str = "deterministic") -> component.Spec:
    return component.Spec(ingress=ingress, drafter=drafter)


class TestConfig:

    def test_a_config_carries_the_ingress_and_the_drafter(self) -> None:
        config = component.Config(_spec(ingress="http://localhost:8080", drafter="deterministic"))

        assert (config.ingress, config.drafter) == ("http://localhost:8080", "deterministic")
