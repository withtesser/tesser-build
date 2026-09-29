from __future__ import annotations

import time
import uuid

import tesser.testing as ts


class TestCliHost:

    def test_a_created_widget_is_found_once_its_name_is_approved(self) -> None:
        name = "w-" + str(uuid.uuid4())
        host = ts.Cli("srv.cli.main")
        created = host.run("create", name)
        found_before_approval = host.run("find", name)
        approved = host.run("approve", name)
        for _ in range(50):
            if approved.exit_code == 0 or "HTTP 412" not in approved.stderr:
                break
            time.sleep(0.1)
            approved = host.run("approve", name)
        found = found_before_approval
        for _ in range(50):
            found = host.run("find", name)
            if found.lines() == ("yes",):
                break
            time.sleep(0.1)
        assert (created.exit_code, created.lines()) == (0, (name,)), created.stderr
        assert (approved.exit_code, approved.lines()) == (0, (name,)), approved.stderr
        assert (found_before_approval.lines(), found.lines()) == (("no",), ("yes",))
