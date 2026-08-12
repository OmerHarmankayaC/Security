"""cozum ipucu sutunu

SDD 4.2.4: "Girdi ile cikti ayri sutunlarda durur." `gecici_sonuc`
durdurulmus bir isin CIKTISI, `cozum_ipucu` yeni bir isin GIRDISIDIR.

Ilk uygulamada ipucu, yeni isin kendi `gecici_sonuc` alaninda tasiniyordu.
Ayni cozum nesnesini tasidiklari icin bu mumkun, fakat o alan iki ayri
sozlesmeye baglanmis olur: ayni deger bir iste "kullanici karari bekliyor",
baska bir iste "modele verilecek ipucu" anlamina gelir. Alanin dolulugana
bakan her sorgu bu iki hali ayirt etmek zorunda kalir ve ayirt etmeyi
unutan sorgu, henuz baslamamis bir isi karar bekliyor sanar.

Revision ID: c9a4b7e21f38
Revises: b6e2f81d3c07
Create Date: 2026-08-12 08:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c9a4b7e21f38"
down_revision: Union[str, None] = "b6e2f81d3c07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cozum_isi", sa.Column("cozum_ipucu", postgresql.JSONB(), nullable=True))
    # Veri tasima YOK. Ipucu yalnizca CALISAN bir isin girdisidir ve gocun
    # uygulandigi anda calisan bir is varsa o zaten kendi surecinde,
    # modelini kurmus haldedir. Devredilecek bir gecmis deger yok.


def downgrade() -> None:
    op.drop_column("cozum_isi", "cozum_ipucu")
