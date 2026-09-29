from __future__ import annotations

import jtbds.domain as domain


class TestJobToBeDone:

    def test_a_job_to_be_done_constructs_from_its_spec(self) -> None:
        job_to_be_done_spec = domain.JobToBeDoneSpec(jtbd_id="jtbd-1", description="design new feature", status="drafting")

        job_to_be_done = domain.JobToBeDone(job_to_be_done_spec)

        assert str(job_to_be_done.identity) == job_to_be_done_spec.jtbd_id
        assert str(job_to_be_done.description) == job_to_be_done_spec.description
        assert str(job_to_be_done.status) == job_to_be_done_spec.status


class TestJtbdId:

    def test_a_jtbd_id_equals_by_value(self) -> None:
        first = domain.JtbdId("jtbd-1")
        second = domain.JtbdId("jtbd-1")

        assert first == second
        assert first != domain.JtbdId("jtbd-2")
