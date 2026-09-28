from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error as urllib_error
import urllib.request as urllib_request


class TestHttpHost:

    def test_the_mounted_restate_endpoint_discovers_the_actions_services_and_the_orchestrator_workflow(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        env = dict(os.environ, STORY_DRAFTING_WRITER="fixed", RESTATE_INGRESS="http://localhost:8080", PYTHONPATH=os.pathsep.join(sys.path))
        host = subprocess.Popen([sys.executable, "-m", "srv.http.main", f"127.0.0.1:{port}"], env=env)
        discover = urllib_request.Request(
            f"http://127.0.0.1:{port}/restate/discover",
            headers={"Accept": "application/vnd.restate.endpointmanifest.v4+json"},
        )
        manifest: dict[str, object] = {}
        try:
            for _ in range(100):
                try:
                    with urllib_request.urlopen(discover, timeout=1) as answer:
                        manifest = json.loads(answer.read())
                    break
                except OSError:
                    time.sleep(0.1)
        finally:
            host.send_signal(signal.SIGINT)
            try:
                host.wait(timeout=10)
            except subprocess.TimeoutExpired:
                host.kill()
                host.wait()

        services = manifest["services"]
        assert isinstance(services, list)
        assert {s["name"]: sorted(h["name"] for h in s["handlers"]) for s in services} == {
            "RunActions": ["record_run"],
            "StoryWritingActions": ["write_stories"],
            "RunOrchestrator": ["draft_stories"],
        }

    def test_the_runs_routes_answer_by_what_they_meet(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with socket.socket() as closed:
            closed.bind(("127.0.0.1", 0))
            unreachable = closed.getsockname()[1]
        env = dict(os.environ, STORY_DRAFTING_WRITER="fixed", RESTATE_INGRESS=f"http://127.0.0.1:{unreachable}", PYTHONPATH=os.pathsep.join(sys.path))
        host = subprocess.Popen([sys.executable, "-m", "srv.http.main", f"127.0.0.1:{port}"], env=env)
        answers: list[int] = []
        try:
            for sent in (
                urllib_request.Request(f"http://127.0.0.1:{port}/runs", data=b"{}", method="POST"),
                urllib_request.Request(f"http://127.0.0.1:{port}/runs", data=b'{"job": "plan a migration"}', method="POST"),
                urllib_request.Request(f"http://127.0.0.1:{port}/runs/never-opened", method="GET"),
            ):
                for _ in range(100):
                    try:
                        with urllib_request.urlopen(sent, timeout=5) as answer:
                            answers.append(answer.status)
                        break
                    except urllib_error.HTTPError as e:
                        answers.append(e.code)
                        break
                    except OSError:
                        time.sleep(0.1)
        finally:
            host.send_signal(signal.SIGINT)
            try:
                host.wait(timeout=10)
            except subprocess.TimeoutExpired:
                host.kill()
                host.wait()

        assert answers == [400, 500, 404]
