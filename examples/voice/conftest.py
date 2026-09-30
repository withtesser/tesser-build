import contextlib
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time
import typing

import httpx
import pytest
import restate.harness as restate_harness
import testcontainers.community.postgres as testcontainers_postgres

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
for _rel in (("..",), ("..", ".."), ("..", "..", "..")):
    _candidate = os.path.abspath(os.path.join(_root, *_rel, "tesser-py"))
    if os.path.isdir(_candidate):
        sys.path.insert(0, _candidate)
        break
else:
    raise RuntimeError(f"no tesser-py at ../, ../../ or ../../../ from {_root}")

RESTATE_IMAGE: typing.Final[str] = "docker.io/restatedev/restate:1.7"
POSTGRES_IMAGE: typing.Final[str] = "docker.io/library/postgres:16"
DEADLINE_SECONDS: typing.Final[float] = 30.0
LIVEKIT_CREDENTIALS: typing.Final[tuple[str, ...]] = (
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "LIVEKIT_AGENT_NAME",
)
LIVEKIT_MODELS: typing.Final[tuple[str, ...]] = ("LIVEKIT_STT_MODEL", "LIVEKIT_TTS_MODEL")


@pytest.fixture(scope="session")
def engine() -> typing.Iterator[restate_harness.RestateContainer]:
    with private_engine() as container:
        yield container


@pytest.fixture(scope="session")
def engine_url(engine: restate_harness.RestateContainer) -> str:
    return f"http://{engine.get_container_host_ip()}:{engine.get_exposed_port(8080)}"


@pytest.fixture(scope="session")
def engine_admin_url(engine: restate_harness.RestateContainer) -> str:
    return f"http://{engine.get_container_host_ip()}:{engine.get_exposed_port(9070)}"


@pytest.fixture(scope="session")
def engine_callback_host() -> str:
    return "host.docker.internal"


@pytest.fixture(scope="session")
def postgres_dsn() -> typing.Iterator[str]:
    with private_postgres() as container:
        yield str(container.get_connection_url(driver=None))


@pytest.fixture(scope="session")
def voice_evals() -> None:
    if os.environ.get("VOICE_EVALS") != "1":
        pytest.skip("set VOICE_EVALS=1 with LiveKit credentials and a unique LIVEKIT_AGENT_NAME to run the evals")


@pytest.fixture(scope="session")
def livekit_environ(voice_evals: None) -> dict[str, str]:
    missing = [name for name in LIVEKIT_CREDENTIALS if not os.environ.get(name)]
    if missing:
        pytest.fail(f"VOICE_EVALS=1 needs {', '.join(missing)}")
    return {name: os.environ[name] for name in (*LIVEKIT_CREDENTIALS, *LIVEKIT_MODELS) if name in os.environ}


@pytest.fixture(scope="session")
def host_engine_url(livekit_environ: dict[str, str], postgres_dsn: str) -> typing.Iterator[str]:
    with private_engine() as host_engine:
        url = f"http://{host_engine.get_container_host_ip()}:{host_engine.get_exposed_port(8080)}"
        port = unused_port()
        served = subprocess.Popen(
            [sys.executable, "-m", "srv.restate.main", f"0.0.0.0:{port}"],
            cwd=pathlib.Path(__file__).resolve().parent,
            env={
                **os.environ,
                **livekit_environ,
                "PYTHONPATH": os.pathsep.join(sys.path),
                "CALLS_STORAGE": postgres_dsn,
                "RESTATE_URL": url,
            },
            start_new_session=True,
        )
        with watchdog(["kill", "-KILL", f"-{served.pid}"]):
            try:
                register(
                    served,
                    f"http://{host_engine.get_container_host_ip()}:{host_engine.get_exposed_port(9070)}",
                    f"http://host.docker.internal:{port}",
                )
                yield url
            finally:
                os.killpg(served.pid, signal.SIGKILL)
                served.wait()


@pytest.fixture(scope="session")
def agent_server(livekit_environ: dict[str, str], postgres_dsn: str, host_engine_url: str) -> typing.Iterator[str]:
    served = subprocess.Popen(
        [sys.executable, "-m", "srv.livekit.agent_server"],
        cwd=pathlib.Path(__file__).resolve().parent,
        env={
            **os.environ,
            **livekit_environ,
            "PYTHONPATH": os.pathsep.join(sys.path),
            "CALLS_STORAGE": postgres_dsn,
            "RESTATE_URL": host_engine_url,
        },
        start_new_session=True,
    )
    with watchdog(["kill", "-KILL", f"-{served.pid}"]):
        try:
            yield livekit_environ["LIVEKIT_AGENT_NAME"]
        finally:
            os.killpg(served.pid, signal.SIGKILL)
            served.wait()


@pytest.fixture
def free_port() -> int:
    return unused_port()


def unused_port() -> int:
    with socket.socket() as probe:
        probe.bind(("0.0.0.0", 0))
        return int(probe.getsockname()[1])


def register(served: subprocess.Popen[bytes], admin_url: str, uri: str) -> None:
    deadline = time.monotonic() + DEADLINE_SECONDS
    answer = ""
    while time.monotonic() < deadline:
        if served.poll() is not None:
            pytest.fail(f"the host exited with {served.returncode} before it could be registered")
        try:
            registered = httpx.post(f"{admin_url}/deployments", json={"uri": uri}, timeout=5.0)
        except httpx.HTTPError as not_yet:
            answer = repr(not_yet)
        else:
            if registered.is_success:
                return
            answer = registered.text
        time.sleep(0.2)
    pytest.fail(f"could not register {uri} at {admin_url} within {DEADLINE_SECONDS}s: {answer}")


@contextlib.contextmanager
def private_engine() -> typing.Iterator[restate_harness.RestateContainer]:
    with restate_harness.create_restate_container(restate_image=RESTATE_IMAGE) as container:
        with watchdog(["docker", "rm", "-f", str(container.get_wrapped_container().id)]):
            yield container


@contextlib.contextmanager
def private_postgres() -> typing.Iterator[testcontainers_postgres.PostgresContainer]:
    with testcontainers_postgres.PostgresContainer(POSTGRES_IMAGE, driver=None) as container:
        with watchdog(["docker", "rm", "-f", str(container.get_wrapped_container().id)]):
            yield container


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
