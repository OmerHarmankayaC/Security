from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import ayarlar

engine = create_engine(ayarlar.veritabani_url, pool_pre_ping=True)
OturumYerel = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def oturum_al() -> Generator[Session, None, None]:
    """FastAPI bagimliligi: istek basariyla bitince islemi onaylar, hata
    halinde geri alir. Servis katmani commit cagirmaz (SDD 3.2: 'Bir servis
    metodunun baslattigi veritabani islemi ... ya butunuyle islenir ya da
    butunuyle geri alinir')."""
    oturum = OturumYerel()
    try:
        yield oturum
        oturum.commit()
    except Exception:
        oturum.rollback()
        raise
    finally:
        oturum.close()
