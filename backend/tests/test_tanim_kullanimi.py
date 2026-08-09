"""Tanim kullanim sayimi (madde 1).

Buradaki testler canli veritabani GEREKTIRMEZ; SQLAlchemy ust verisi uzerinde
calisirlar. Sorgu davranisi test_tanim_api.py'de dogrulanir.
"""

from app.db import Base
from app.services.tanim_kullanimi import kaynaklari_getir, sayilan_modeller


def _tanima_isaret_eden_yabanci_anahtarlar(model: type[Base]) -> set[str]:
    """Modelin birincil anahtarina isaret eden butun FK sutunlari, 'tablo.sutun'."""
    hedef_tablo = model.__tablename__
    bulunanlar: set[str] = set()
    for tablo in Base.metadata.tables.values():
        for sutun in tablo.columns:
            for fk in sutun.foreign_keys:
                if fk.column.table.name == hedef_tablo:
                    bulunanlar.add(f"{tablo.name}.{sutun.name}")
    return bulunanlar


def test_her_tanim_icin_butun_yabanci_anahtarlar_sayiliyor() -> None:
    """Kullanim sayimi, tanima isaret eden HER yabanci anahtari kapsamali.

    Kapsanmayan bir referans iki hatayi birden dogurur: kullanim sifir
    gorunur, tanim silinmeye calisilir ve silme yabanci anahtar kisitina
    duser. Yeni bir tablo bir tanima baglandiginda bu test kirilir.
    """
    for model in sayilan_modeller():
        sayilanlar = {
            f"{kaynak.sutun.parent.tables[0].name}.{kaynak.sutun.key}"
            for kaynak in kaynaklari_getir(model)
        }
        beklenen = _tanima_isaret_eden_yabanci_anahtarlar(model)
        assert sayilanlar == beklenen, (
            f"{model.__tablename__}: sayimda eksik {beklenen - sayilanlar}, "
            f"fazladan {sayilanlar - beklenen}"
        )


def test_kayit_turu_adlari_teknik_terim_degil() -> None:
    """NFR-5: kullaniciya gosterilen metin operasyon dilinde olmali.

    Onay kutusunda bu adlar dogrudan gecer ("42 atamada kullanılıyor"), o
    yuzden tablo/sutun adi sizmamali.
    """
    for model in sayilan_modeller():
        for kaynak in kaynaklari_getir(model):
            assert "_" not in kaynak.kayit_turu, kaynak.kayit_turu
            assert kaynak.kayit_turu == kaynak.kayit_turu.lower(), kaynak.kayit_turu


def test_personel_disindaki_tanimlar_aktif_bayragi_tasiyor() -> None:
    """Pasiflestirme `aktif` bayragi uzerinden yurur; personel istisnadir
    (aktiflik orada tarih araligiyla ifade edilir, SDD 4.2.1)."""
    for model in sayilan_modeller():
        if model.__tablename__ == "personel":
            assert "aktif_bitis" in model.__table__.columns
            continue
        assert "aktif" in model.__table__.columns, model.__tablename__
