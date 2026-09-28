from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request as urllib_request


class TestRestateHost:

    def test_the_served_endpoint_discovers_the_workflow_and_its_actions(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with tempfile.TemporaryDirectory() as storage:
            env = dict(
                os.environ,
                STORY_DRAFTING_STORAGE=storage,
                RESTATE_INGRESS="http://ingress.invalid:8080",
                STORY_DRAFTING_DRAFTER="deterministic",
                PYTHONPATH=os.pathsep.join(sys.path),
            )
            host = subprocess.Popen([sys.executable, "-m", "srv.restate.main", f"127.0.0.1:{port}"], env=env)
            discover = urllib_request.Request(
                f"http://127.0.0.1:{port}/discover",
                headers={"Accept": "application/vnd.restate.endpointmanifest.v4+json"},
            )
            manifest: dict[str, object] = {}
            for _ in range(100):
                try:
                    with urllib_request.urlopen(discover, timeout=1) as answer:
                        manifest = json.loads(answer.read())
                    break
                except OSError:
                    time.sleep(0.1)
            host.send_signal(signal.SIGINT)
            try:
                host.wait(timeout=10)
            except subprocess.TimeoutExpired:
                host.kill()
                host.wait()
        services = manifest["services"]
        assert isinstance(services, list)
        assert {s["name"]: sorted(h["name"] for h in s["handlers"]) for s in services} == {
            "RunOrchestrator": ["conduct_run"],
            "DraftingActions": ["draft_stories"],
            "RunActions": ["record_run"],
        }
