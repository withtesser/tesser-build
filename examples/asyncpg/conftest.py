import contextlib
import os
import subprocess
import sys
import time
import typing

import pytest
import testcontainers.core.container as testcontainers_container

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
for _rel in (("..",), ("..", ".."), ("..", "..", "..")):
    _candidate = os.path.abspath(os.path.join(_root, *_rel, "tesser-py"))
    if os.path.isdir(_candidate):
        sys.path.insert(0, _candidate)
        break
else:
    raise RuntimeError(f"no tesser-py at ../, ../../ or ../../../ from {_root}")

DEADLINE_SECONDS: typing.Final[float] = 30.0
POSTGRES_IMAGE: typing.Final[str] = "docker.io/library/postgres:16"
POSTGRES_USER: typing.Final[str] = "tesser"
POSTGRES_DB: typing.Final[str] = "tesser"


@pytest.fixture(scope="session")
def storage_url() -> typing.Iterator[str]:
    with private_postgres() as dsn:
        yield dsn


@contextlib.contextmanager
def private_postgres() -> typing.Iterator[str]:
    container = (
        testcontainers_container.DockerContainer(POSTGRES_IMAGE)
        .with_env("POSTGRES_USER", POSTGRES_USER)
        .with_env("POSTGRES_DB", POSTGRES_DB)
        .with_env("POSTGRES_HOST_AUTH_METHOD", "trust")
        .with_exposed_ports(5432)
    )
    with container:
        with watchdog(["docker", "rm", "-f", str(container.get_wrapped_container().id)]):
            deadline = time.monotonic() + DEADLINE_SECONDS
            ready = container.exec(["pg_isready", "--host", "127.0.0.1", "--username", POSTGRES_USER])
            while ready.exit_code != 0 and time.monotonic() < deadline:
                time.sleep(0.2)
                ready = container.exec(["pg_isready", "--host", "127.0.0.1", "--username", POSTGRES_USER])
            if ready.exit_code != 0:
                pytest.fail(f"postgres was not ready within {DEADLINE_SECONDS}s: {ready.output!r}")
            yield (
                f"postgres://{POSTGRES_USER}@{container.get_container_host_ip()}:"
                f"{container.get_exposed_port(5432)}/{POSTGRES_DB}"
            )


@contextlib.contextmanager
def watchdog(command: list[str]) -> typing.Iterator[None]:
    guard = subprocess.Popen(
        ["sh", "-c", 'cat >/dev/null; exec "$@"', "watchdog", *command],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        yield
    finally:
        guard.kill()
        guard.wait()
