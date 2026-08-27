"""Ortam beyaninin sozlesmesi (Demo Senaryosu 10)."""

from pydantic import BaseModel


class OrtamOku(BaseModel):
    #: Acikken arayuz gosterim seridini cizer. Ayarin kendisi
    #: `app/config.py`'de tanimlidir ve ortam degiskeninden okunur.
    demo_kipi: bool = False


__all__ = ["OrtamOku"]
