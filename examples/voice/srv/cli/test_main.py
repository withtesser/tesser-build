from __future__ import annotations

import os
import subprocess
import sys


class TestCliHost:

    def test_get_call_for_a_call_that_was_never_placed_exits_one_with_the_contexts_wording(
        self, storage_url: str, engine_url: str
    ) -> None:
        env = {
            **os.environ,
            "LIVEKIT_URL": "ws://livekit.invalid",
            "LIVEKIT_API_KEY": "unused",
            "LIVEKIT_API_SECRET": "unused",
            "LIVEKIT_AGENT_NAME": "caller",
            "PYTHONPATH": os.pathsep.join(sys.path),
            "CALLS_STORAGE": storage_url,
            "RESTATE_URL": engine_url,
        }

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", "get-call", "cli-never-placed"],
            capture_output=True, text=True, check=False, env=env, timeout=60.0,
        )

        assert completed.returncode == 1, completed.stderr
        assert completed.stdout == "no call 'cli-never-placed'\n"

    def test_an_unknown_command_or_a_missing_argument_exits_two_with_the_usage(
        self, storage_url: str, engine_url: str
    ) -> None:
        env = {
            **os.environ,
            "LIVEKIT_URL": "ws://livekit.invalid",
            "LIVEKIT_API_KEY": "unused",
            "LIVEKIT_API_SECRET": "unused",
            "LIVEKIT_AGENT_NAME": "caller",
            "PYTHONPATH": os.pathsep.join(sys.path),
            "CALLS_STORAGE": storage_url,
            "RESTATE_URL": engine_url,
        }

        completed = [
            subprocess.run(
                [sys.executable, "-m", "srv.cli.main", *argv],
                capture_output=True, text=True, check=False, env=env, timeout=60.0,
            )
            for argv in ([], ["hang-up"], ["get-call"])
        ]
        printed = "".join(run.stdout for run in completed)

        assert [run.returncode for run in completed] == [2, 2, 2], [run.stderr for run in completed]
        assert printed.count("usage: place-call | get-call <call_id>\n") == 2
        assert "missing argument <call_id>\nusage: get-call <call_id>\n" in printed

    def test_an_unexpected_failure_exits_one_and_leaks_nothing_to_stdout(self) -> None:
        env = {name: value for name, value in os.environ.items() if name != "CALLS_STORAGE"}
        env.update(
            {
                "PYTHONPATH": os.pathsep.join(sys.path),
                "RESTATE_URL": "http://engine.invalid:8080",
                "LIVEKIT_URL": "ws://livekit.invalid",
                "LIVEKIT_API_KEY": "unused",
                "LIVEKIT_API_SECRET": "unused",
                "LIVEKIT_AGENT_NAME": "caller",
            }
        )

        completed = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", "get-call", "c7"],
            capture_output=True, text=True, check=False, env=env, timeout=60.0,
        )

        assert completed.returncode == 1
        assert completed.stdout == "unexpected error\n"
        assert "CALLS_STORAGE is required" in completed.stderr
