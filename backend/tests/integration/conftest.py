from collections.abc import Iterator

import pytest
from testcontainers.community.oracle import OracleDbContainer


@pytest.fixture(scope="session")
def oracle_url() -> Iterator[str]:
    with OracleDbContainer() as oracle:
        yield oracle.get_connection_url()
