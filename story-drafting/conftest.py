import os
import random
import sys
import typing

import pytest
import restate.harness as restate_harness

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


@pytest.fixture(scope="session", autouse=True)
def engine() -> typing.Iterator[None]:
    if "RESTATE_INGRESS" in os.environ:
        yield
        return
    with restate_harness.create_restate_container(restate_image=RESTATE_IMAGE) as container:
        os.environ.update(
            RESTATE_INGRESS=f"http://{container.get_container_host_ip()}:{container.get_exposed_port(8080)}",
            RESTATE_ADMIN=f"http://{container.get_container_host_ip()}:{container.get_exposed_port(9070)}",
            STORY_DRAFTING_CALLBACK_HOST="host.docker.internal",
            RESTATE_CALLBACK_HOST="host.docker.internal",
            STORY_WRITER="canned",
            STORY_DRAFTING_PORT=str(random.randrange(20000, 60000)),
        )
        yield
