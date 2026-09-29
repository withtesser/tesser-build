from __future__ import annotations

import drafting.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", status="pending")

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.identity) == jtbd_spec.jtbd_id
        assert str(jtbd.status) == jtbd_spec.status


class TestJtbdId:

    def test_a_jtbd_id_equals_by_value(self) -> None:
        first = domain.JtbdId("jtbd-1")
        second = domain.JtbdId("jtbd-1")

        assert first == second
        assert first != domain.JtbdId("jtbd-2")
