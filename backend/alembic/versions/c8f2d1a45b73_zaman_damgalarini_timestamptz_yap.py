"""zaman damgalarini timestamptz yap

Butun zaman damgasi sutunlari TIMESTAMP WITHOUT TIME ZONE idi; uygulama ise
her yere datetime.now(UTC) yaziyordu. Saat dilimi bilgisi sutunda
saklanmadigi icin JSON'a ofsetsiz bir dize olarak cikiyor ve istemci
tarafinin bunu YEREL saat sanmasi riski doguyordu (frontend bunu
utcTarihiAyristir ile 'Z' ekleyerek telafi ediyordu).

MEVCUT VERININ YORUMU. Var olan degerler UTC kabul edilir - uygulama zaten
UTC yazdigi icin dogru olan budur. Donusum bu yuzden ACIKCA yazilir:

    USING <kolon> AT TIME ZONE 'UTC'

Bu ifade birakilirsa PostgreSQL sunucunun `TimeZone` ayarini varsayar ve
degerleri sessizce kaydirir (Turkiye'de uc saat). ALTER TYPE tek seferlik
bir donusumdur; yanlis yapilirsa geri alinamaz, o yuzden burada acik.

KAPSAM. Asagidaki 35 sutun, 16 tablo (app/models altindan uretildi):

    atama               olusturma_zamani, guncelleme_zamani
    bina                olusturma_zamani, guncelleme_zamani
    cizelge_surumu      yayin_zamani, olusturma_zamani, guncelleme_zamani
    cozum_isi           baslangic_zamani, bitis_zamani,
                        olusturma_zamani, guncelleme_zamani
    donem               olusturma_zamani, guncelleme_zamani
    gorev_noktasi       olusturma_zamani, guncelleme_zamani
    kapsama_acigi       olusturma_zamani, guncelleme_zamani
    kural               olusturma_zamani, guncelleme_zamani
    musaitlik           olusturma_zamani, guncelleme_zamani
    ozel_gun            olusturma_zamani, guncelleme_zamani
    personel            olusturma_zamani, guncelleme_zamani
    personel_yetkinlik  olusturma_zamani, guncelleme_zamani
    talep               olusturma_zamani, guncelleme_zamani
    tercih              olusturma_zamani, guncelleme_zamani
    vardiya_tipi        olusturma_zamani, guncelleme_zamani
    yetkinlik           olusturma_zamani, guncelleme_zamani

Not: tarih (DATE) sutunlari - donem.baslangic_tarihi, atama.tarih,
musaitlik tarihleri vb. - KAPSAM DISIDIR. Onlar bir takvim gunudur, bir
zaman anı degil; saat dilimi tasimalari anlamsiz olurdu (TD-1).

Revision ID: c8f2d1a45b73
Revises: a1c3f7e9b2d4
Create Date: 2026-08-08 09:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8f2d1a45b73"
down_revision: Union[str, None] = "a1c3f7e9b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tablo, sutun, nullable)
_SUTUNLAR: list[tuple[str, str, bool]] = [
    ("atama", "olusturma_zamani", False),
    ("atama", "guncelleme_zamani", False),
    ("bina", "olusturma_zamani", False),
    ("bina", "guncelleme_zamani", False),
    ("cizelge_surumu", "yayin_zamani", True),
    ("cizelge_surumu", "olusturma_zamani", False),
    ("cizelge_surumu", "guncelleme_zamani", False),
    ("cozum_isi", "baslangic_zamani", False),
    ("cozum_isi", "bitis_zamani", True),
    ("cozum_isi", "olusturma_zamani", False),
    ("cozum_isi", "guncelleme_zamani", False),
    ("donem", "olusturma_zamani", False),
    ("donem", "guncelleme_zamani", False),
    ("gorev_noktasi", "olusturma_zamani", False),
    ("gorev_noktasi", "guncelleme_zamani", False),
    ("kapsama_acigi", "olusturma_zamani", False),
    ("kapsama_acigi", "guncelleme_zamani", False),
    ("kural", "olusturma_zamani", False),
    ("kural", "guncelleme_zamani", False),
    ("musaitlik", "olusturma_zamani", False),
    ("musaitlik", "guncelleme_zamani", False),
    ("ozel_gun", "olusturma_zamani", False),
    ("ozel_gun", "guncelleme_zamani", False),
    ("personel", "olusturma_zamani", False),
    ("personel", "guncelleme_zamani", False),
    ("personel_yetkinlik", "olusturma_zamani", False),
    ("personel_yetkinlik", "guncelleme_zamani", False),
    ("talep", "olusturma_zamani", False),
    ("talep", "guncelleme_zamani", False),
    ("tercih", "olusturma_zamani", False),
    ("tercih", "guncelleme_zamani", False),
    ("vardiya_tipi", "olusturma_zamani", False),
    ("vardiya_tipi", "guncelleme_zamani", False),
    ("yetkinlik", "olusturma_zamani", False),
    ("yetkinlik", "guncelleme_zamani", False),
]


def upgrade() -> None:
    for tablo, sutun, nullable in _SUTUNLAR:
        op.alter_column(
            tablo,
            sutun,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=nullable,
            # Mevcut degerler UTC'dir (uygulama datetime.now(UTC) yaziyor).
            postgresql_using=f"{sutun} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for tablo, sutun, nullable in _SUTUNLAR:
        op.alter_column(
            tablo,
            sutun,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=nullable,
            # Ters yon: saat dilimli degeri UTC duvarina cevirerek yaz,
            # boylece upgrade/downgrade cifti degeri degistirmez.
            postgresql_using=f"{sutun} AT TIME ZONE 'UTC'",
        )
