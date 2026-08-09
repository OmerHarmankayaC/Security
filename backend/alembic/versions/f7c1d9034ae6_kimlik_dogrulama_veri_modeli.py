"""kimlik dogrulama veri modeli: kullanici ve oturum

SDD 4.2.1'deki iki tabloyu kurar. Ikisi de YENI tablodur; mevcut hicbir
tablonun sutunu degismez, dolayisiyla goc geriye donuk uyumludur ve canli
sistemde veri donusumu gerektirmez.

`kullanici.personel_id` yabanci anahtari `personel`e bakar ve NULL
birakilabilir - yonetici ve yonetim rollerinin personel kaydi olmayabilir.
CHECK kisiti bu serbestligi calisan rolunde kapatir (FR-10.6): rol CALISAN
ise personel_id dolu olmak ZORUNDADIR. Kisit veritabaninda durur cunku
ihlalinin sonucu eksik bir alan degil, kimin verisini gorecegi belirsiz bir
calisan hesabidir - FR-9.1'in dayandigi baglantinin kendisi.

Ikinci CHECK kisiti kullanici adini KUCUK HARFE zorlar. Benzersizlik kisiti
tek basina "Ahmet" ile "ahmet"i ayni saymaz; giris yolu kullanici adini
kucuk harfe cevirip esledigi icin saklanan degerin de kucuk harf oldugu
garanti altina alinir. Aksi halde ayni kisi icin iki satir dogar ve
hangisine girildigi yaziliska baglanirdi.

`oturum.oturum_id` belirtecin OZETIDIR, belirtecin kendisi degil (SDD 5.1b).
Bu yuzden VARCHAR(64): SHA-256 onaltilik gosterimi. Belirtec yalniz cerezde
durur; veritabani okunsa bile acik oturumlar ele gecirilemez.

`oturum.kullanici_id` uzerinde ON DELETE CASCADE var ama bu, hesap silmeyi
ima ETMEZ - hesaplar silinmez, devre disi birakilir (FR-10.5). Kaskad
yalnizca kalintili oturum satiri kalmasin diyedir.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7c1d9034ae6"
down_revision: Union[str, None] = "e3b81f47a95c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kullanici",
        sa.Column("kullanici_id", sa.Integer(), nullable=False),
        sa.Column("kullanici_adi", sa.String(), nullable=False),
        sa.Column("parola_ozeti", sa.String(), nullable=False),
        sa.Column(
            "rol",
            sa.Enum("CALISAN", "YONETICI", "YONETIM", name="rol"),
            nullable=False,
        ),
        sa.Column("personel_id", sa.Integer(), nullable=True),
        sa.Column(
            "parola_degistirmeli", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("aktif", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "basarisiz_deneme", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("kilit_bitis", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "olusturma_zamani",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "guncelleme_zamani",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rol <> 'CALISAN' OR personel_id IS NOT NULL",
            name="ck_kullanici_calisan_personele_bagli",
        ),
        sa.CheckConstraint(
            "kullanici_adi = lower(kullanici_adi)",
            name="ck_kullanici_adi_kucuk_harf",
        ),
        sa.ForeignKeyConstraint(["personel_id"], ["personel.personel_id"]),
        sa.PrimaryKeyConstraint("kullanici_id"),
        sa.UniqueConstraint("kullanici_adi"),
    )
    op.create_table(
        "oturum",
        sa.Column("oturum_id", sa.String(length=64), nullable=False),
        sa.Column("kullanici_id", sa.Integer(), nullable=False),
        sa.Column("olusturma", sa.DateTime(timezone=True), nullable=False),
        sa.Column("son_erisim", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gecerlilik_bitis", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["kullanici_id"], ["kullanici.kullanici_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("oturum_id"),
    )
    op.create_index("ix_oturum_kullanici_id", "oturum", ["kullanici_id"])


def downgrade() -> None:
    op.drop_index("ix_oturum_kullanici_id", table_name="oturum")
    op.drop_table("oturum")
    op.drop_table("kullanici")
    sa.Enum(name="rol").drop(op.get_bind(), checkfirst=True)
