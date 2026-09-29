from __future__ import annotations

import story_drafting.domain as domain


class TestJobToBeDone:

    def test_a_job_to_be_done_constructs_from_its_spec(self) -> None:
        job_to_be_done_spec = domain.JobToBeDoneSpec(jtbd_id="jtbd-1", statement="When I plan a trip I want an itinerary", step="drafting", draft_count=1, picked_draft="As a traveller I want an itinerary")

        job_to_be_done = domain.JobToBeDone(job_to_be_done_spec)

        assert str(job_to_be_done.identity) == job_to_be_done_spec.jtbd_id
        assert str(job_to_be_done.statement) == job_to_be_done_spec.statement
        assert str(job_to_be_done.step) == job_to_be_done_spec.step
        assert int(job_to_be_done.draft_count) == job_to_be_done_spec.draft_count
        assert str(job_to_be_done.picked_draft) == job_to_be_done_spec.picked_draft


class TestJtbdId:

    def test_a_jtbd_id_equals_by_value(self) -> None:
        first = domain.JtbdId("jtbd-1")
        second = domain.JtbdId("jtbd-1")

        assert first == second
        assert first != domain.JtbdId("jtbd-2")
