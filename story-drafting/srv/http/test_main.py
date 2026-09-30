from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error as urllib_error
import urllib.request as urllib_request

import app as app


class TestHttpHost:

    def test_the_mounted_restate_endpoint_discovers_what_the_context_declared(self, free_port: int) -> None:
        port = free_port
        env = dict(os.environ, RESTATE_URL="http://localhost:8080", STORY_WRITER="canned", PYTHONPATH=os.pathsep.join(sys.path))
        host = subprocess.Popen([sys.executable, "-m", "srv.http.main", f"127.0.0.1:{port}"], env=env)
        try:
            discover = urllib_request.Request(
                f"http://127.0.0.1:{port}/restate/discover",
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
        finally:
            host.send_signal(signal.SIGINT)
            try:
                host.wait(timeout=10)
            except subprocess.TimeoutExpired:
                host.kill()
                host.wait()
        story_drafting_app = app.AppLoader(app.EnvConfigRepository({"RESTATE_URL": "http://localhost:8080", "STORY_WRITER": "canned"})).load()
        try:
            declared = {
                story_drafting_app.drafting.run_actions_service.name: sorted(
                    story_drafting_app.drafting.run_actions_service.handlers
                ),
                story_drafting_app.drafting.story_actions_service.name: sorted(
                    story_drafting_app.drafting.story_actions_service.handlers
                ),
                story_drafting_app.drafting.run_orchestrator_workflow.name: sorted(
                    story_drafting_app.drafting.run_orchestrator_workflow.handlers
                ),
            }
        finally:
            story_drafting_app.close()
        services = manifest["services"]
        assert isinstance(services, list)
        assert {s["name"]: sorted(h["name"] for h in s["handlers"]) for s in services} == declared

    def test_the_runs_routes_answer_by_the_failure_they_meet(self, free_port: int) -> None:
        port = free_port
        env = dict(os.environ, RESTATE_URL="http://127.0.0.1:9", STORY_WRITER="canned", PYTHONPATH=os.pathsep.join(sys.path))
        host = subprocess.Popen([sys.executable, "-m", "srv.http.main", f"127.0.0.1:{port}"], env=env)
        answers: list[int] = []
        try:
            for method, path, body in (
                ("POST", "/runs", b'{"run_id": "r1"}'),
                ("POST", "/runs", b'{"run_id": "r1", "job": " "}'),
                ("POST", "/runs", b'{"run_id": "r1", "job": "ship"}'),
                ("GET", "/runs/r1", None),
                ("GET", "/runs/..", None),
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
        assert answers == [400, 422, 500, 404, 422]
