from __future__ import annotations

import json

import tesser.application as ts

import drafting.domain as domain
import tesser.errors as errors


class RunSnapshot(ts.Serde):

    def serialize(self, run: domain.Run) -> bytes:
        return json.dumps(
            {
                "run_id": str(run.identity),
                "job": str(run.job),
                "stage": str(run.stage),
                "stories": [{"text": str(story)} for story in run.stories],
                "accepted_stories": [{"text": str(story)} for story in run.accepted_stories],
            }
        ).encode()

    def deserialize(self, buf: bytes) -> domain.Run:
        snapshot = json.loads(buf)
        if not (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("run_id"), str)
            and isinstance(snapshot.get("job"), str)
            and isinstance(snapshot.get("stage"), str)
            and isinstance(snapshot.get("stories"), list)
            and all(isinstance(story, dict) and isinstance(story.get("text"), str) for story in snapshot["stories"])
            and isinstance(snapshot.get("accepted_stories"), list)
            and all(isinstance(story, dict) and isinstance(story.get("text"), str) for story in snapshot["accepted_stories"])
        ):
            raise errors.invalid("invalid_snapshot", "a run snapshot is a run_id, a job, a stage, and its stories")
        return domain.Run(
            domain.RunSpec(
                run_id=snapshot["run_id"],
                job=snapshot["job"],
                stage=snapshot["stage"],
                stories=tuple(domain.StorySpec(text=story["text"]) for story in snapshot["stories"]),
                accepted_stories=tuple(domain.StorySpec(text=story["text"]) for story in snapshot["accepted_stories"]),
            )
        )
