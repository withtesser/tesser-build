import os


def served(variable: str) -> str:
    address = os.environ.get(variable)
    if not address:
        raise LookupError(f"{variable} is not set; the runner serves the host and names its address in {variable}")
    return address
