from __future__ import annotations

import pytest

import drafting.application.snapshots as snapshots
import drafting.domain as domain
import tesser.errors as errors


class TestRunSnapshot:

    def test_a_run_comes_back_whole(self) -> None:
        run = domain.Run(
            domain.RunSpec(
                run_id="r1",
                job="ship the release",
                stage="awaiting_pick",
                stories=(domain.StorySpec(text="As a developer, I want a release"),),
                accepted_stories=(),
            )
        )
        rebuilt = snapshots.RunSnapshot().deserialize(snapshots.RunSnapshot().serialize(run))
        assert rebuilt.identity == run.identity
        assert rebuilt.job == run.job
        assert rebuilt.stage == run.stage
        assert rebuilt.stories == run.stories
        assert rebuilt.accepted_stories == run.accepted_stories

    def test_a_snapshot_missing_its_stories_is_invalid(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            snapshots.RunSnapshot().deserialize(b'{"run_id": "r1", "job": "ship", "stage": "drafting"}')
        assert excinfo.value.code == "invalid_snapshot"

    def test_a_snapshot_the_domain_refuses_is_refused(self) -> None:
        with pytest.raises(errors.DomainError) as excinfo:
            snapshots.RunSnapshot().deserialize(
                b'{"run_id": "r1", "job": "", "stage": "drafting", "stories": [], "accepted_stories": []}'
            )
        assert excinfo.value.code == "empty_job"
