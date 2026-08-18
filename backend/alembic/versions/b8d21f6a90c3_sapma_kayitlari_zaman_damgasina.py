"""sapma kayitlari zaman damgasina (B-23, SRS 7.2)

Revision ID: b8d21f6a90c3
Revises: a3f5d81c7e42

`kapsama_acigi` ve `fazla_kadro` tablolari `tarih` (DATE) + `baslangic`/`bitis`
(TIME) yerine `baslangic_zamani`/`bitis_zamani` (TIMESTAMPTZ) tasir. `atama`
tablosu ayni bicime Tur 5'te gecmisti; bu ikisi geride kalmisti.

NEDEN. Tarih + ofsetsiz saat gosterimi iki seyi birden yapamiyordu:
gece yarisini asan bir araligi (22.00-02.00) TEK kayitta tutmak ve disa
aktarmada ISO damgasi uretmek. Ikincisi icin saklanmayan bir ofsetin
uydurulmasi gerekirdi; birincisi yuzunden birlestirici gun sinirinda kesmek
zorundaydi ve tek bir acik dosyada iki acik gibi gorunuyordu.

MEVCUT KAYITLAR DONUSTURULMEZ, SILINIR. Bu iki tablo bir COZUMUN CIKTISIDIR,
kullanicinin girdigi veri degil: surum yeniden cozuldugunde ya da elle
duzenlendiginde `sapmalari_yenile` tarafindan dogru bicimde yeniden yazilir.
Ayni karar Tur 3'te talep gocunde de verildi ve gerekcesi aynidir - yanlis
donusmus bir acik kaydi hic olmamasindan kotudur, cunku rapora dogru gibi
girer ve kimse sorgulamaz.

Geri alma da ayni sekilde: sutunlar geri gelir, satirlar gelmez.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8d21f6a90c3"
down_revision: str | None = "a3f5d81c7e42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLOLAR = ("kapsama_acigi", "fazla_kadro")


def upgrade() -> None:
    for tablo in _TABLOLAR:
        # Once satirlar dusurulur: yeni sutunlar NOT NULL ve dolduracak
        # dogru bir deger YOK. Bos tabloda kisitlar sorunsuz kurulur.
        op.execute(sa.text(f"DELETE FROM {tablo}"))
        op.drop_column(tablo, "tarih")
        op.drop_column(tablo, "baslangic")
        op.drop_column(tablo, "bitis")
        op.add_column(
            tablo, sa.Column("baslangic_zamani", sa.TIMESTAMP(timezone=True), nullable=False)
        )
        op.add_column(
            tablo, sa.Column("bitis_zamani", sa.TIMESTAMP(timezone=True), nullable=False)
        )


def downgrade() -> None:
    for tablo in _TABLOLAR:
        op.execute(sa.text(f"DELETE FROM {tablo}"))
        op.drop_column(tablo, "baslangic_zamani")
        op.drop_column(tablo, "bitis_zamani")
        op.add_column(tablo, sa.Column("tarih", sa.Date(), nullable=False))
        op.add_column(tablo, sa.Column("baslangic", sa.Time(), nullable=False))
        op.add_column(tablo, sa.Column("bitis", sa.Time(), nullable=False))
