# pragma: tesser-generated; regenerate from the composition, never edit by hand
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
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
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
            "StoryActions": ["draft_stories"],
            "JtbdActions": ["record_stories"],
            "JtbdOrchestrator": ["draft_jtbd_stories"],
        }

    def test_the_routes_answer_by_the_failure_they_meet(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with socket.socket() as closed:
            closed.bind(("127.0.0.1", 0))
            unreachable = closed.getsockname()[1]
        env = dict(
            os.environ, RESTATE_INGRESS=f"http://127.0.0.1:{unreachable}", PYTHONPATH=os.pathsep.join(sys.path)
        )
        host = subprocess.Popen([sys.executable, "-m", "srv.http.main", f"127.0.0.1:{port}"], env=env)
        answers: list[int] = []

        try:
            for method, path, body in (
                ("POST", "/jtbds", b"{}"),
                ("POST", "/jtbds", b'{"role": "a developer", "i_want": "to keep my place", "so_that": "I can step away"}'),
                ("GET", "/jtbds/never-issued", None),
            ):
                request = urllib_request.Request(
                    f"http://127.0.0.1:{port}{path}",
                    data=body,
                    method=method,
                    headers={"Content-Type": "application/json"},
                )
                for _ in range(100):
                    try:
                        with urllib_request.urlopen(request, timeout=5) as answer:
                            answers.append(answer.status)
                        break
                    except urllib_error.HTTPError as error:
                        answers.append(error.code)
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

        assert answers == [400, 500, 500]
