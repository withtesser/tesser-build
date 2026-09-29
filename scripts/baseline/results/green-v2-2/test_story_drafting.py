from __future__ import annotations

import json
import time
import urllib.error as urllib_error
import urllib.request as urllib_request
import uuid

import tesser.testing as ts


class TestDraftingStories:

    def test_a_started_run_waits_for_my_pick_with_its_drafted_stories_and_none_accepted(self) -> None:
        host = ts.served("STORY_DRAFTING_HOST")
        job = (
            "When I work through a multi-step piece of work with an agent, I want its checkpoints fixed "
            f"in advance, so I can step away and pick up where we were ({uuid.uuid4()})"
        )
        start = urllib_request.Request(
            f"{host}/runs",
            data=json.dumps({"job": job}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(start, timeout=30) as answer:
            started_status = answer.status
            started = json.loads(answer.read())
        run_id = started["run_id"]

        run: dict[str, object] = {}
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and run.get("stage") != "awaiting_pick":
            try:
                with urllib_request.urlopen(f"{host}/runs/{run_id}", timeout=5) as answer:
                    run = json.loads(answer.read())
            except urllib_error.HTTPError as e:
                if e.code != 404:
                    raise
            time.sleep(0.2)

        assert started_status == 202
        assert (run.get("run_id"), run.get("job")) == (run_id, job), "the started run never read back through the host"
        assert run.get("stage") == "awaiting_pick"
        stories = run.get("stories")
        assert isinstance(stories, list) and stories, "the run has no drafted stories to pick from"
        assert run.get("accepted_stories") == []
