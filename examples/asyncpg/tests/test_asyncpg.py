from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import uuid

import protocol


class TestCliHost:

    def test_an_added_part_is_stored_and_a_second_add_of_its_name_is_refused(self) -> None:
        tree = pathlib.Path(__file__).resolve().parent.parent
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        name = f"e2e-{uuid.uuid4().hex}"
        taken_request = protocol.CliRequest(args=(f"{name}-taken", "p"))
        held_request = protocol.CliRequest(args=(name, name))
        repeated_request = protocol.CliRequest(args=(name, "q"))
        taken = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", *taken_request.args],
            cwd=tree, env=env, capture_output=True, text=True, check=False,
        )
        held = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", *held_request.args],
            cwd=tree, env=env, capture_output=True, text=True, check=False,
        )
        repeated = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", *repeated_request.args],
            cwd=tree, env=env, capture_output=True, text=True, check=False,
        )
        assert protocol.CliResponse(
            exit_code=taken.returncode, line=protocol.Line(text=taken.stdout.strip())
        ) == protocol.CliResponse(exit_code=0, line=protocol.Line(text=f"{name}-taken p kept"))
        assert protocol.CliResponse(
            exit_code=held.returncode, line=protocol.Line(text=held.stdout.strip())
        ) == protocol.CliResponse(exit_code=0, line=protocol.Line(text=f"{name} {name} released"))
        assert protocol.CliResponse(
            exit_code=repeated.returncode, line=protocol.Line(text=repeated.stdout.strip())
        ) == protocol.CliResponse(
            exit_code=1, line=protocol.Line(text=f"widget {name!r} is already stored")
        )
