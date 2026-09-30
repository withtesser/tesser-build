from __future__ import annotations

import json
import time
import urllib.request as urllib_request
import uuid

import tesser.testing as ts


class TestReadingAJobToBeDoneWhoseStoriesAreDrafted:

    def test_reading_it_answers_200_awaiting_story_acceptance_with_its_drafted_stories(self) -> None:
        submit = urllib_request.Request(
            f"{ts.served('STORY_DRAFTING_HOST')}/jtbds",
            data=json.dumps(
                {
                    "role": "a developer working through a multi-step piece of work with an agent",
                    "i_want": "the steps and the checkpoints where I weigh in to be fixed in advance " + uuid.uuid4().hex,
                    "so_that": "I can step away, come back, and pick up at the step we were on",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(submit, timeout=30) as answer:
            jtbd_id = json.loads(answer.read())["jtbd_id"]
        for _ in range(40):
            with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
                polled = json.loads(answer.read())
            if polled.get("status") == "awaiting_story_acceptance":
                break
            time.sleep(0.25)

        with urllib_request.urlopen(f"{ts.served('STORY_DRAFTING_HOST')}/jtbds/{jtbd_id}", timeout=30) as answer:
            status = answer.status
            read = json.loads(answer.read())

        assert status == 200
        assert read.get("status") == "awaiting_story_acceptance"
        stories = read.get("stories", [])
        assert len(stories) >= 1
        assert all(
            all(isinstance(story.get(part), str) and story[part] for part in ("given", "when", "then"))
            for story in stories
        )
        assert all(story.get("state") == "drafted" for story in stories)
