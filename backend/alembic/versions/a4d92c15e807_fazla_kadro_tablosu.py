"""fazla kadro tablosu

Bir gorev noktasina TALEPTEN FAZLA kisi atanmis olmasini kalici hale
getirir. SRS 4.3 S1 bu ust siniri "zorunlu" tanimlar ve `modele_ekle`
cozucuye oyle ekler; dolayisiyla COZUCU boyle bir satir hicbir zaman
uretmez. Kaynagi tektir: MANUEL duzenleme (SDD 5.5 / 6.3.3 uyarinca elle
yapilan degisiklikte esnek bulgular engellemez, bildirilir).

NEDEN AYRI TABLO, `kapsama_acigi`'na `tur` sutunu DEGIL:

  1. SDD 4.2.4 `kapsama_acigi`'ni "S1 formulasyonundaki eksik
     degiskenlerinin sifirdan buyuk oldugu ucluleerin DOGRUDAN karsiligi"
     diye tanimlar - cozucu degiskeniyle birebir. Fazla kadronun cozucude
     karsiligi yoktur: amac fonksiyonunda (SRS 4.4) terimi yok ve cozucu
     onu yapisal olarak uretemez. Ayni tabloya konmasi, o birebirligi
     bozardi.
  2. Kod tabaninda otuz bir dosya `kapsama_acigi`'ni "her satir bir
     ACIKTIR" varsayimiyla okuyor. `tur` sutunu eklemek bu sorgularin
     TUMUNUN anlamini sessizce degistirirdi; tek bir filtrenin atlanmasi
     kapsama oranini, yazdirma gorunumunu ya da Ozet ekranini fazla
     kadroyu acik sayar hale getirirdi. Ayri tablo bu hata bicimini
     yapisal olarak ortadan kaldirir.
  3. Karsilikli dislayicilik yine korunur: bir hucre ayni anda hem eksik
     hem fazla olamaz ve iki tablo da tek gecliste, ayni
     `atanan - gereken` karsilastirmasindan yazilir
     (app/services/talep_sapmasi.py).

Sema `kapsama_acigi` ile ayni sekli tasir; tek fark sayinin adidir
(`fazla_sayi`). Goc EKLEMELIDIR: mevcut hicbir tablo degismez, veri
donusumu yoktur, geri alinabilir.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4d92c15e807"
down_revision: Union[str, None] = "f7c1d9034ae6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fazla_kadro",
        sa.Column("fazla_id", sa.Integer(), nullable=False),
        sa.Column("surum_id", sa.Integer(), nullable=False),
        sa.Column("tarih", sa.Date(), nullable=False),
        sa.Column("vardiya_tipi_id", sa.Integer(), nullable=False),
        sa.Column("nokta_id", sa.Integer(), nullable=False),
        sa.Column("fazla_sayi", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["surum_id"], ["cizelge_surumu.surum_id"]),
        sa.ForeignKeyConstraint(["vardiya_tipi_id"], ["vardiya_tipi.vardiya_tipi_id"]),
        sa.ForeignKeyConstraint(["nokta_id"], ["gorev_noktasi.nokta_id"]),
        sa.PrimaryKeyConstraint("fazla_id"),
    )
    op.create_index("ix_fazla_kadro_surum_id", "fazla_kadro", ["surum_id"])


def downgrade() -> None:
    op.drop_index("ix_fazla_kadro_surum_id", table_name="fazla_kadro")
    op.drop_table("fazla_kadro")
