"""tercih tablosunda (personel_id, tarih) tekilligi

Revision ID: c4f1a7d20b93
Revises: b8d21f6a90c3
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "c4f1a7d20b93"
down_revision: str | Sequence[str] | None = "b8d21f6a90c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _riskli_gruplari_bul(kopyalar: Sequence[Any]) -> list[Any]:
    """Final review bulgu 3: bir kopya grubu, icinde BEKLEMEDE-DISI (yani
    yonetici tarafindan KARARLANMIS -- onaylanmis/reddedilmis) bir satir
    varsa RISKLIDIR. Eski silme kurali ("en yeni tercih_id kalir") KAYIT
    SIRASINI esas alir, KARARI degil -- onaylanmis bir tercihten SONRA
    bekleyen bir tercih girildiyse, onaylanmis (ve cozucunun girdisi olan)
    kayit sessizce silinirdi.

    Saf fonksiyon (DB baglantisi almaz): satirlarin yalniz `durum` alani
    okunur, boylece hem gercek SQLAlchemy Row nesneleriyle (upgrade icinde)
    hem elle kurulmus basit nesnelerle (testte) calisir.
    """
    return [s for s in kopyalar if any(d != "BEKLEMEDE" for d in s.durumlar)]


def upgrade() -> None:
    baglanti = op.get_bind()
    # (a) SAYIM once ve GORUNUR: kac satirin gidecegi VE hangi KARARLARIN
    # riske girdigi bilinmeden kisit konulmaz. `durum` da tasinir --
    # yalniz "kac kopya var" degil "bunlardan biri KARARLANMIS mi" sorusu
    # asagidaki kapi icin sart. Cikti dagitim gunlugune ve PROGRESS_V2'ye
    # gecer.
    # `durum::text` SART: `durum` veritabaninda ISIMLI bir enum tipidir
    # (`tercihdurumu`) ve psycopg bu OZEL dizi tipini otomatik COZEMEDIGI
    # icin cast'siz `array_agg(durum)` bir Python listesi degil, tek bir
    # dize ("{ONAYLANDI,BEKLEMEDE}") dondurur -- asagidaki karsilastirma
    # o zaman dizenin TEK TEK KARAKTERLERini gezer, hicbiri "BEKLEMEDE"
    # dizesine esit olamayacagi icin HER kopya grubu (guvenli olanlar
    # dahil) yanlislikla riskli isaretlenirdi. `text` doknown bir dizi
    # tipi oldugundan psycopg onu duzgun bir listeye cozer.
    kopyalar = baglanti.execute(
        sa.text(
            "SELECT personel_id, tarih, count(*) AS adet, "
            "array_agg(durum::text ORDER BY tercih_id) AS durumlar FROM tercih "
            "GROUP BY personel_id, tarih HAVING count(*) > 1 ORDER BY personel_id, tarih"
        )
    ).fetchall()
    for satir in kopyalar:
        print(
            f"[goc c4f1a7d20b93] kopya: personel={satir.personel_id} "
            f"tarih={satir.tarih} adet={satir.adet} durumlar={list(satir.durumlar)}"
        )

    # (b) GUVENLIK KAPISI: herhangi bir kopya grubunda BEKLEMEDE-DISI bir
    # satir varsa goc BURADA DURUR -- hicbir satir silinmez, kisit de
    # konulmaz. `downgrade` silinen satirlari GERI GETIREMEDIGI icin
    # (asagida) otomatik silme, geri donulemez bir yonetici kararini
    # sessizce yok edebilirdi (final review bulgu 3, senaryo: personel 7 /
    # 2026-09-03'te tercih_id=41 ONAYLANDI, tercih_id=58 BEKLEMEDE --
    # eski kural 41'i siler, onaylanmis giridi cozucuden sessizce dusurur).
    riskli = _riskli_gruplari_bul(kopyalar)
    if riskli:
        ciftler = ", ".join(f"(personel_id={s.personel_id}, tarih={s.tarih})" for s in riskli)
        raise RuntimeError(
            "[goc c4f1a7d20b93] DURDURULDU: asagidaki (personel_id, tarih) "
            "ciftlerinde kopya grubunun icinde BEKLEMEDE-DISI (onaylanmis/"
            f"reddedilmis) en az bir kayit var: {ciftler}. Bu gruplar "
            "OTOMATIK silinmez -- operatorun elle inceleyip hangi kaydin "
            "kalacagina karar vermesi gerekir (bkz. PROGRESS_V2.md, "
            "'Dagitim oncesi sayim' basligi)."
        )

    # (c) Buraya gelindiyse butun kopya gruplari TAMAMEN BEKLEMEDE'dir;
    # onceki davranis (en yeni tercih_id kalir) guvenle uygulanabilir --
    # hicbir yonetici karari riske girmez.
    silinen = baglanti.execute(
        sa.text(
            "DELETE FROM tercih t USING tercih y "
            "WHERE t.personel_id = y.personel_id AND t.tarih = y.tarih "
            "AND t.tercih_id < y.tercih_id RETURNING t.tercih_id"
        )
    ).fetchall()
    print(f"[goc c4f1a7d20b93] silinen kopya satir: {len(silinen)} -> {[s.tercih_id for s in silinen]}")
    # (d) Kisit en sona: temizlik yapilmadan konulursa goc patlardi.
    op.create_unique_constraint("uq_tercih_personel_tarih", "tercih", ["personel_id", "tarih"])


def downgrade() -> None:
    # Silinen kopyalar GERI GELMEZ; downgrade yalniz kisiti kaldirir.
    op.drop_constraint("uq_tercih_personel_tarih", "tercih", type_="unique")
