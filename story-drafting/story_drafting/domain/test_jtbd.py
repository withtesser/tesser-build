from __future__ import annotations

import story_drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", job="When I design a feature, I want sign-off fixed in advance, so I can step away")

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.identity) == jtbd_spec.jtbd_id
        assert str(jtbd.job) == jtbd_spec.job


class TestJtbdId:

    def test_a_jtbd_id_equals_by_value(self) -> None:
        first = domain.JtbdId("jtbd-1")
        second = domain.JtbdId("jtbd-1")

        assert first == second
        assert first != domain.JtbdId("jtbd-2")
