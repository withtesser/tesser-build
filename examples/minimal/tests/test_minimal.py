from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid

class TestCliHost:

    def test_a_created_widget_is_found_once_its_name_is_approved(self) -> None:
        name = "w-" + str(uuid.uuid4())
        tree = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        environment = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        host = [sys.executable, "-m", "srv.cli.main"]
        created = subprocess.run([*host, "create", name], cwd=tree, env=environment, capture_output=True, text=True, check=False)
        found_before_approval = subprocess.run([*host, "find", name], cwd=tree, env=environment, capture_output=True, text=True, check=False)
        approved = subprocess.run([*host, "approve", name], cwd=tree, env=environment, capture_output=True, text=True, check=False)
        found = found_before_approval
        for _ in range(50):
            found = subprocess.run([*host, "find", name], cwd=tree, env=environment, capture_output=True, text=True, check=False)
            if found.stdout == "yes\n":
                break
            time.sleep(0.1)
        assert (created.returncode, created.stdout) == (0, name + "\n"), created.stderr
        assert (approved.returncode, approved.stdout) == (0, name + "\n"), approved.stderr
        assert (found_before_approval.stdout, found.stdout) == ("no\n", "yes\n")
