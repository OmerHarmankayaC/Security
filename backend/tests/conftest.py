"""Testler arasi paylasilan yardimcilar: canli PostgreSQL gerektiren testler icin atlama."""

import pytest
from sqlalchemy.exc import OperationalError

from app.db import engine


def pg_yoksa_atla() -> None:
    """Yerel PostgreSQL'e baglanilamiyorsa testi atlar (bkz. README "Kurulum")."""
    try:
        with engine.connect():
            pass
    except OperationalError:
        pytest.skip("Yerel PostgreSQL sunucusuna baglanilamadi")
