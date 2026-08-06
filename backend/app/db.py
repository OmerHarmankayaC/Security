from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import ayarlar

engine = create_engine(ayarlar.veritabani_url, pool_pre_ping=True)
OturumYerel = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def oturum_al() -> Generator[Session, None, None]:
    oturum = OturumYerel()
    try:
        yield oturum
    finally:
        oturum.close()
