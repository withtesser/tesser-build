import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--host", help="the base URL of the served host, named by the runner")


@pytest.fixture(scope="session")
def host(request: pytest.FixtureRequest) -> str:
    address = request.config.getoption("--host")
    if not address:
        pytest.fail("pass --host <url>: the runner serves the host and names its address")
    return str(address)
