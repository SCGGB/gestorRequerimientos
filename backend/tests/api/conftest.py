from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from tests.api.helpers import build_client


@pytest.fixture
def client() -> TestClient:
    """Cliente autenticado con todos los roles (para pruebas que no miden auth)."""
    return build_client()


@pytest.fixture
def client_as() -> Callable[..., TestClient]:
    """Fábrica de clientes autenticados con los roles indicados."""
    return build_client
