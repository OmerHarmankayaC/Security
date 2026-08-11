"""durdurma karari alanlari

Durdurma artik tek yonlu bir iptal degil (SRS FR-4.9, FR-4.10; SDD 4.2.4,
5.4.1): arama sonlanir, bulunmus cozum saklanir ve kullanici karar verir.
Bunun icin uc ekleme:

    cozum_isi.durum          ENUM'a `DURDURULDU` degeri
    cozum_isi.gecici_sonuc   JSONB NULL
    cozum_isi.devam_kaynagi_is_id  INT NULL, kendine FK

`DURDURULDU` TERMINAL BIR DURUM DEGILDIR - is, karar verilene kadar orada
bekler. `kullan` karari onu tamamlandi/uyarili'ya, `at` ve `devam`
kararlari iptal'e goturur.

ENUM degeri `COZULUYOR`dan sonraya yerlestirilir; siralama modeldeki
tanimla ayni kalsin diye (davranissal etkisi yok, yalnizca ORDER BY ve
karsilastirma sirasini belirler).

`bitis_zamani` TIMESTAMPTZ MI? SDD 4.2.4 onu TIMESTAMPTZ olarak
tanimliyor. Kontrol edildi: sutun zaten timestamptz - goc c8f2d1a45b73
(zaman damgalarini timestamptz yap) cozum_isi.baslangic_zamani ve
bitis_zamani'ni o turda cevirmisti. Bu yuzden burada bir donusum YOK;
olmayan bir farki "duzeltmek" icin ALTER TYPE yazmak, mevcut degerleri
ikinci kez yorumlama riski dogururdu.

Revision ID: b6e2f81d3c07
Revises: a4d92c15e807
Create Date: 2026-08-11 22:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b6e2f81d3c07"
down_revision: Union[str, None] = "a4d92c15e807"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL 12+ ALTER TYPE ... ADD VALUE'yu islem icinde kabul eder;
    # yeni deger AYNI islemde KULLANILAMAZ. Burada yalnizca tanimlaniyor,
    # kullanan yok - dolayisiyla sorun degil.
    op.execute("ALTER TYPE cozumisidurumu ADD VALUE IF NOT EXISTS 'DURDURULDU' AFTER 'COZULUYOR'")
    op.add_column("cozum_isi", sa.Column("gecici_sonuc", postgresql.JSONB(), nullable=True))
    op.add_column("cozum_isi", sa.Column("devam_kaynagi_is_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_cozum_isi_devam_kaynagi",
        "cozum_isi",
        "cozum_isi",
        ["devam_kaynagi_is_id"],
        ["is_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_cozum_isi_devam_kaynagi", "cozum_isi", type_="foreignkey")
    op.drop_column("cozum_isi", "devam_kaynagi_is_id")
    op.drop_column("cozum_isi", "gecici_sonuc")
    # ENUM degeri GERI ALINMAZ. PostgreSQL'de bir enum degerini kaldirmanin
    # yolu tipi bastan yaratip butun bagimli sutunlari cevirmektir; o
    # islem, DURDURULDU durumunda bekleyen bir is varsa veri kaybettirir.
    # Kullanilmayan bir enum degeri ise hicbir seye mal olmaz.
