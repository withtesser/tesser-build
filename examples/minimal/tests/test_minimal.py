from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid


class TestCliHost:

    def test_a_created_widget_is_found_once_its_name_is_approved(self, host_engine_url: str, storage_url: str) -> None:
        name = "w-" + str(uuid.uuid4())
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path), "RESTATE_URL": host_engine_url, "ALPHA_STORAGE": storage_url, "BETA_KEY": "k"}
        created = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", "create", name],
            capture_output=True, text=True, check=False, env=env,
        )
        found_before_approval = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", "find", name],
            capture_output=True, text=True, check=False, env=env,
        )
        approved = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", "approve", name],
            capture_output=True, text=True, check=False, env=env,
        )
        for _ in range(50):
            if approved.returncode == 0 or "HTTP 412" not in approved.stderr:
                break
            time.sleep(0.1)
            approved = subprocess.run(
                [sys.executable, "-m", "srv.cli.main", "approve", name],
                capture_output=True, text=True, check=False, env=env,
            )
        found = found_before_approval
        for _ in range(50):
            found = subprocess.run(
                [sys.executable, "-m", "srv.cli.main", "find", name],
                capture_output=True, text=True, check=False, env=env,
            )
            if found.stdout.splitlines() == ["yes"]:
                break
            time.sleep(0.1)
        assert (created.returncode, created.stdout.splitlines()) == (0, [name]), created.stderr
        assert (approved.returncode, approved.stdout.splitlines()) == (0, [name]), approved.stderr
        assert (found_before_approval.stdout.splitlines(), found.stdout.splitlines()) == (["no"], ["yes"])
