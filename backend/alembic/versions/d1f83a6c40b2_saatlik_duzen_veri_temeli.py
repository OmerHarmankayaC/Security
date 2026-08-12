"""saatlik duzen veri temeli

Saatlik calisma duzenine gecisin VERI temeli (SRS 3.3.4, TD-13; SDD 4.2.1,
4.2.2, 4.2.4). Kural katalogu bu gocte DEGISMEZ.

Uc degisiklik:

1. `talep` bir calisma bloguna degil bir ZAMAN ARALIGINA baglanir:
   `vardiya_tipi_id` yerine `baslangic` ve `bitis`. Mevcut satirlar bagli
   olduklari blogun saatlerini alir.
2. `kapsama_acigi` ve `fazla_kadro` da aralik tasir. Bu iki tabloda VERI
   TASINMAZ, satirlar SILINIR - gerekcesi asagida.
3. `personel` kaydina devir bakiyesi alanlari eklenir.

GUN SONU `00.00` ILE GOSTERILIR. SDD 4.2.2 bunun icin `24.00` yaziyor;
PostgreSQL o degeri saklayabiliyor ama surucu (psycopg) `datetime.time`
24:00 tasiyamadigi icin geri okuyamiyor - denendi, `DataError: hour must be
in 0..23`. Bunun yerine `vardiya_tipi` tablosunda ZATEN kullanilan sozlesme
uygulanir: `bitis <= baslangic` ise aralik gun sonuna kadar surer. Yeni bir
kavram girmez.

DONUSUM SAYILARAK DOGRULANIR. Talep satirlarinin donusumunde iki buyukluk
karsilastirilir - satir sayisi ve toplam KISI-SAAT yuku - ve esit
degillerse goc HATA VERIR. Sessizce devam etmesi hâlinde kaybolan bir
talep satiri hicbir yerde gorunmezdi: talep dustugu icin kapsama acigi da
dogmaz ve hiçbir rapor bunu bildirmez.

NEDEN ACIK/FAZLA KADRO SATIRLARI SILINIYOR. Bu iki tablo bir cozumun
CIKTISIDIR, kullanicinin girdigi veri degil. Blok eksenli bir acik kaydini
aralik eksenine cevirmek, o kaydin uretildigi andaki talebi yeniden
kurmayi gerektirir; talep ise ayni gocte degisiyor. Satirlar surumun
yeniden cozulmesiyle ya da elle duzenlenmesiyle dogru bicimde yeniden
yazilir (`sapmalari_yenile`). Yanlis donusmus bir acik kaydi, hic
olmamasindan daha kotudur: rapora dogru gibi girer.

Revision ID: d1f83a6c40b2
Revises: c9a4b7e21f38
Create Date: 2026-08-12 10:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1f83a6c40b2"
down_revision: Union[str, None] = "c9a4b7e21f38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _kisi_saat_yuku_blok(baglanti: sa.Connection) -> int:
    """Blok eksenli talebin toplam kisi-saat yuku: Σ gereken_sayi × sure_saat."""
    return (
        baglanti.execute(
            sa.text("""
            SELECT COALESCE(SUM(t.gereken_sayi * v.sure_saat), 0)
              FROM talep t
              JOIN vardiya_tipi v ON v.vardiya_tipi_id = t.vardiya_tipi_id
        """)
        ).scalar()
        or 0
    )


def _kisi_saat_yuku_aralik(baglanti: sa.Connection) -> int:
    """Aralik eksenli talebin toplam kisi-saat yuku: Σ gereken_sayi × aralik_suresi.

    `bitis <= baslangic` gun sonuna (ya da ertesi gune) tasan araligi
    gosterir; suresi 24 saatten geriye sayilarak bulunur.
    """
    return (
        baglanti.execute(
            sa.text("""
            SELECT COALESCE(SUM(
                     gereken_sayi *
                     CASE WHEN bitis > baslangic
                          THEN EXTRACT(EPOCH FROM (bitis - baslangic)) / 3600
                          ELSE 24 - EXTRACT(EPOCH FROM (baslangic - bitis)) / 3600
                     END), 0)
              FROM talep
        """)
        ).scalar()
        or 0
    )


def upgrade() -> None:
    baglanti = op.get_bind()

    # --- talep: blok -> aralik ---------------------------------------------
    onceki_satir = baglanti.execute(sa.text("SELECT COUNT(*) FROM talep")).scalar()
    onceki_yuk = _kisi_saat_yuku_blok(baglanti)

    op.add_column("talep", sa.Column("baslangic", sa.Time(), nullable=True))
    op.add_column("talep", sa.Column("bitis", sa.Time(), nullable=True))
    baglanti.execute(
        sa.text("""
        UPDATE talep t
           SET baslangic = v.baslangic_saati,
               bitis      = v.bitis_saati
          FROM vardiya_tipi v
         WHERE v.vardiya_tipi_id = t.vardiya_tipi_id
    """)
    )

    doldurulmayan = baglanti.execute(
        sa.text("SELECT COUNT(*) FROM talep WHERE baslangic IS NULL OR bitis IS NULL")
    ).scalar()
    if doldurulmayan:
        raise RuntimeError(
            f"{doldurulmayan} talep satiri donusturulemedi (vardiya tipi bulunamadi); "
            "goc geri alindi."
        )

    op.alter_column("talep", "baslangic", nullable=False)
    op.alter_column("talep", "bitis", nullable=False)
    op.drop_constraint("talep_vardiya_tipi_id_fkey", "talep", type_="foreignkey")
    op.drop_column("talep", "vardiya_tipi_id")

    sonraki_satir = baglanti.execute(sa.text("SELECT COUNT(*) FROM talep")).scalar()
    sonraki_yuk = _kisi_saat_yuku_aralik(baglanti)
    if onceki_satir != sonraki_satir:
        raise RuntimeError(
            f"Talep satir sayisi degisti: {onceki_satir} -> {sonraki_satir}; goc geri alindi."
        )
    if round(float(onceki_yuk), 2) != round(float(sonraki_yuk), 2):
        raise RuntimeError(
            f"Talep kisi-saat yuku degisti: {onceki_yuk} -> {sonraki_yuk}; goc geri alindi."
        )

    # --- kapsama_acigi / fazla_kadro: blok -> aralik ------------------------
    # Cozum ciktisi olduklari icin donusturulmez, silinir (bkz. baslik).
    baglanti.execute(sa.text("DELETE FROM kapsama_acigi"))
    baglanti.execute(sa.text("DELETE FROM fazla_kadro"))
    for tablo in ("kapsama_acigi", "fazla_kadro"):
        op.add_column(tablo, sa.Column("baslangic", sa.Time(), nullable=False))
        op.add_column(tablo, sa.Column("bitis", sa.Time(), nullable=False))
        op.drop_constraint(f"{tablo}_vardiya_tipi_id_fkey", tablo, type_="foreignkey")
        op.drop_column(tablo, "vardiya_tipi_id")

    # --- personel: devir bakiyesi -------------------------------------------
    op.add_column(
        "personel",
        sa.Column(
            "devir_fazla_calisma_saat",
            sa.Numeric(6, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column("personel", sa.Column("kota_yili", sa.Integer(), nullable=True))

    # --- cozum_isi: on kontrol bulgulari kalici -----------------------------
    # Bulgular artik isi dusurmuyor (SDD 5.2, K18); sonucla birlikte
    # gosterilmeleri ve surum raporunda kalmalari gerekiyor.
    op.add_column(
        "cozum_isi", sa.Column("on_kontrol_bulgulari", postgresql.JSONB(), nullable=True)
    )


def downgrade() -> None:
    baglanti = op.get_bind()

    op.drop_column("cozum_isi", "on_kontrol_bulgulari")

    op.drop_column("personel", "kota_yili")
    op.drop_column("personel", "devir_fazla_calisma_saat")

    # Acik/fazla kadro satirlari geri donusturulemez (yukari yonde de
    # tasinmadilar); tablolar bosaltilarak eski sutun geri alinir.
    for tablo in ("kapsama_acigi", "fazla_kadro"):
        baglanti.execute(sa.text(f"DELETE FROM {tablo}"))
        op.add_column(tablo, sa.Column("vardiya_tipi_id", sa.Integer(), nullable=False))
        op.create_foreign_key(
            f"{tablo}_vardiya_tipi_id_fkey",
            tablo,
            "vardiya_tipi",
            ["vardiya_tipi_id"],
            ["vardiya_tipi_id"],
        )
        op.drop_column(tablo, "bitis")
        op.drop_column(tablo, "baslangic")

    # Talep satirlari, araligiyla BIREBIR eslesen bloga geri baglanir.
    # Eslesme bulunamayan satir varsa geri alma DURUR: satiri sessizce
    # dusurmek talebi azaltir ve bu hicbir raporda gorunmez.
    op.add_column("talep", sa.Column("vardiya_tipi_id", sa.Integer(), nullable=True))
    baglanti.execute(
        sa.text("""
        UPDATE talep t
           SET vardiya_tipi_id = v.vardiya_tipi_id
          FROM vardiya_tipi v
         WHERE v.baslangic_saati = t.baslangic
           AND v.bitis_saati     = t.bitis
    """)
    )
    eslesmeyen = baglanti.execute(
        sa.text("SELECT COUNT(*) FROM talep WHERE vardiya_tipi_id IS NULL")
    ).scalar()
    if eslesmeyen:
        raise RuntimeError(
            f"{eslesmeyen} talep araligi hicbir blokla eslesmiyor; geri alma yapilamaz. "
            "Once bu araliklari blok sinirlarina getirin."
        )
    op.alter_column("talep", "vardiya_tipi_id", nullable=False)
    op.create_foreign_key(
        "talep_vardiya_tipi_id_fkey",
        "talep",
        "vardiya_tipi",
        ["vardiya_tipi_id"],
        ["vardiya_tipi_id"],
    )
    op.drop_column("talep", "bitis")
    op.drop_column("talep", "baslangic")
