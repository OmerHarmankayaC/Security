"""surum duzenleme damgasi (SRS TD-16, SDD 5.5.1)

Revision ID: a3f5d81c7e42
Revises: f2a8c561d94b

`cizelge_surumu.damga`: duzenleme oturumunun basinda alinip kaydederken geri
gonderilen OPAK dize. Damga degismisse baska bir oturum ayni surumu
degistirmis demektir ve kayit reddedilir; sessizce uzerine yazmak digerinin
isini iz birakmadan yok ederdi.

Var olan satirlara birbirinden FARKLI degerler yazilir. Hepsine ayni sabit
yazilsaydi iki ayri surumun damgasi esit cikar ve karsilastirma hicbir sey
ayirt etmezdi; `gen_random_uuid()` satir basina calisir (pgcrypto degil,
PostgreSQL 13+ cekirdeginde).

Sema degisikligi; veri donusturmez. Geri alma sutunu duserir.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a3f5d81c7e42"
down_revision: str | None = "f2a8c561d94b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ONCE NULL olarak eklenir, sonra doldurulur, sonra NOT NULL yapilir.
    # Tek adimda `nullable=False` + `server_default` verilseydi butun satirlar
    # AYNI degeri alirdi (server_default sabit bir ifade olarak bir kez
    # degerlendirilir); damganin isi satirlari ayirt etmektir.
    op.add_column("cizelge_surumu", sa.Column("damga", sa.String(length=36), nullable=True))
    op.execute("UPDATE cizelge_surumu SET damga = gen_random_uuid()::text WHERE damga IS NULL")
    op.alter_column("cizelge_surumu", "damga", nullable=False)


def downgrade() -> None:
    op.drop_column("cizelge_surumu", "damga")
