from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request
import uuid


class TestStartingTheStoryDraftingSkill:

    def test_a_started_run_waits_for_the_developers_pick_with_drafted_stories_and_none_accepted(self, host: str) -> None:
        run_id = str(uuid.uuid4())
        job = (
            "When I work through a multi-step piece of work with an agent, I want the checkpoints fixed in "
            "advance, so I can step away and pick up where we were " + uuid.uuid4().hex
        )
        start = urllib_request.Request(
            f"{host}/runs",
            data=json.dumps({"run_id": run_id, "job": job}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(start, timeout=30) as answer:
            started_status = answer.status
            started = json.loads(answer.read())
        assert started_status == 202
        assert started == {"run_id": run_id}

        run: dict[str, object] = {}
        for _ in range(100):
            try:
                with urllib_request.urlopen(f"{host}/runs/{run_id}", timeout=30) as answer:
                    run = json.loads(answer.read())
            except urllib_error.HTTPError as not_yet:
                if not_yet.code != 404:
                    raise
            if run.get("stage") == "awaiting_pick":
                break
            time.sleep(0.1)
        assert run, f"run {run_id} was never read back through the host"
        assert (run["run_id"], run["job"]) == (run_id, job)

        assert run["stage"] == "awaiting_pick"
        assert isinstance(run["stories"], list) and run["stories"]
        assert run["accepted_stories"] == []
