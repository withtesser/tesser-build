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

RESTATE_IMAGE: typing.Final[str] = "docker.io/restatedev/restate:1.7"
DEADLINE_SECONDS: typing.Final[float] = 30.0


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--host", help="the base URL of a host already served; without it the run serves its own")


@pytest.fixture(scope="session")
def host(request: pytest.FixtureRequest) -> typing.Iterator[str]:
    address = request.config.getoption("--host")
    if address:
        yield str(address)
        return
    with restate_harness.create_restate_container(restate_image=RESTATE_IMAGE) as engine:
        port = free_port()
        served = subprocess.Popen(
            [sys.executable, "-m", "srv.http.main", f"0.0.0.0:{port}"],
            cwd=pathlib.Path(__file__).resolve().parents[1],
            env={**os.environ, "RESTATE_INGRESS": f"http://{engine.get_container_host_ip()}:{engine.get_exposed_port(8080)}", "STORY_WRITER": "canned", "PYTHONPATH": os.pathsep.join(sys.path)},
            start_new_session=True,
        )
        try:
            register(served, f"http://{engine.get_container_host_ip()}:{engine.get_exposed_port(9070)}", f"http://host.docker.internal:{port}/restate")
            yield f"http://127.0.0.1:{port}"
        finally:
            stop(served)


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("0.0.0.0", 0))
        return int(probe.getsockname()[1])


def register(served: subprocess.Popen[bytes], admin: str, uri: str) -> None:
    deadline = time.monotonic() + DEADLINE_SECONDS
    answer = ""
    while time.monotonic() < deadline:
        if served.poll() is not None:
            pytest.fail(f"the host exited with {served.returncode} before it could be registered")
        try:
            registered = httpx.post(f"{admin}/deployments", json={"uri": uri}, timeout=5.0)
        except httpx.HTTPError as not_yet:
            answer = repr(not_yet)
        else:
            if registered.is_success:
                return
            answer = registered.text
        time.sleep(0.2)
    pytest.fail(f"could not register {uri} at {admin} within {DEADLINE_SECONDS}s: {answer}")


def stop(served: subprocess.Popen[bytes]) -> None:
    if served.poll() is None:
        os.killpg(served.pid, signal.SIGTERM)
        try:
            served.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            os.killpg(served.pid, signal.SIGKILL)
            served.wait()
