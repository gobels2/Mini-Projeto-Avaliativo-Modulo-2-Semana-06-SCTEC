"""Fixtures compartilhadas pelos testes do projeto."""
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def dir_raw() -> Path:
    """Diretório com os sete .zip anuais originais do BPS."""
    return RAIZ / "data" / "raw"
