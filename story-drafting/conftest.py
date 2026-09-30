# pragma: tesser-generated; regenerate from the composition, never edit by hand
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

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
for _rel in (("..",), ("..", ".."), ("..", "..", "..")):
    _candidate = os.path.abspath(os.path.join(_root, *_rel, "tesser-py"))
    if os.path.isdir(_candidate):
        sys.path.insert(0, _candidate)
        break

RESTATE_IMAGE: typing.Final[str] = "docker.io/restatedev/restate:1.7"
DEADLINE_SECONDS: typing.Final[float] = 30.0


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--host", help="the base URL of a host already served; without it the run serves its own")


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
def host(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> typing.Iterator[str]:
    address = request.config.getoption("--host")
    if address:
        yield str(address)
        return
    locations = tmp_path_factory.mktemp("locations")
    with private_engine() as host_engine:
        port = unused_port()
        served = subprocess.Popen(
            [sys.executable, "-m", "srv.http.main"],
            cwd=pathlib.Path(__file__).resolve().parent,
            env={
                **os.environ,
                "PYTHONPATH": os.pathsep.join(sys.path),
                "RESTATE_URL": f"http://{host_engine.get_container_host_ip()}:{host_engine.get_exposed_port(8080)}",
                "JTBD_DB_PATH": str(locations / "sqlite_location"),
                "STORY_DRAFTING_PORT": str(port),
            },
            start_new_session=True,
        )
        with watchdog(["kill", "-KILL", f"-{served.pid}"]):
            try:
                register(
                    served,
                    f"http://{host_engine.get_container_host_ip()}:{host_engine.get_exposed_port(9070)}",
                    f"http://host.docker.internal:{port}/restate",
                )
                yield f"http://127.0.0.1:{port}"
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
