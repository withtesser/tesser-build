from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import asyncpg


class TestCliHost:

    def test_the_host_runs_the_command(self, storage_url: str) -> None:
        with asyncio.Runner() as runner:
            connection = runner.run(asyncpg.connect(storage_url))
            runner.run(connection.execute("DROP TABLE IF EXISTS widgets"))
            runner.run(connection.close())
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path), "ALPHA_STORAGE": storage_url, "BETA_STORAGE": storage_url}

        ran = subprocess.run([sys.executable, "-m", "srv.cli.main", "srv-cli", "p"], capture_output=True, text=True, check=False, env=env)

        assert ran.returncode == 0, ran.stderr

    def test_the_host_reports_the_conflict_of_a_second_add(self, storage_url: str) -> None:
        with asyncio.Runner() as runner:
            connection = runner.run(asyncpg.connect(storage_url))
            runner.run(connection.execute("DROP TABLE IF EXISTS widgets"))
            runner.run(connection.close())
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path), "ALPHA_STORAGE": storage_url, "BETA_STORAGE": storage_url}

        first = subprocess.run([sys.executable, "-m", "srv.cli.main", "srv-cli-twice", "p"], capture_output=True, text=True, check=False, env=env)
        second = subprocess.run([sys.executable, "-m", "srv.cli.main", "srv-cli-twice", "p"], capture_output=True, text=True, check=False, env=env)

        assert (first.returncode, second.returncode) == (0, 1), (first.stderr, second.stderr)
