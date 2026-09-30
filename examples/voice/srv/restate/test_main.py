from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request as urllib_request


class TestRestateHost:
    def test_the_served_restate_endpoint_discovers_the_actions_service_and_the_orchestrator_workflow(
        self, storage_url: str, engine_url: str, free_port: int
    ) -> None:
        port = free_port
        env = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join(sys.path),
            "CALLS_STORAGE": storage_url,
            "RESTATE_URL": engine_url,
            "LIVEKIT_URL": "ws://livekit.invalid",
            "LIVEKIT_API_KEY": "unused",
            "LIVEKIT_API_SECRET": "unused",
            "LIVEKIT_AGENT_NAME": "caller",
        }
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
            "CallActions": ["record_call"],
            "CallOrchestrator": ["conduct_call", "person_joined", "person_turn_completed"],
            "DialingActions": ["dial_person", "hang_up"],
            "SpeechActions": ["say_utterance"],
        }
