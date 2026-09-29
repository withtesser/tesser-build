from __future__ import annotations

import jtbds.domain as domain


class TestJtbd:

    def test_a_jtbd_constructs_from_its_spec(self) -> None:
        jtbd_spec = domain.JtbdSpec(jtbd_id="jtbd-1", job="Design a login page, get my sign-off, then build it", step="drafting", draft_count=0, picked_draft="none")

        jtbd = domain.Jtbd(jtbd_spec)

        assert str(jtbd.identity) == jtbd_spec.jtbd_id
        assert str(jtbd.job) == jtbd_spec.job
        assert str(jtbd.step) == jtbd_spec.step
        assert int(jtbd.draft_count) == jtbd_spec.draft_count
        assert str(jtbd.picked_draft) == jtbd_spec.picked_draft


class TestJtbdId:

    def test_a_jtbd_id_equals_by_value(self) -> None:
        first = domain.JtbdId("jtbd-1")
        second = domain.JtbdId("jtbd-1")

        assert first == second
        assert first != domain.JtbdId("jtbd-2")
