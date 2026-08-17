"""tercih tablosunda (personel_id, tarih) tekilligi

Revision ID: c4f1a7d20b93
Revises: b8d21f6a90c3
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4f1a7d20b93"
down_revision: str | Sequence[str] | None = "b8d21f6a90c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    baglanti = op.get_bind()
    # (a) SAYIM once ve GORUNUR: kac satirin gidecegi bilinmeden kisit
    # konulmaz. Cikti dagitim gunlugune ve PROGRESS_V2'ye gecer.
    kopyalar = baglanti.execute(
        sa.text(
            "SELECT personel_id, tarih, count(*) AS adet FROM tercih "
            "GROUP BY personel_id, tarih HAVING count(*) > 1 ORDER BY personel_id, tarih"
        )
    ).fetchall()
    for satir in kopyalar:
        print(
            f"[goc c4f1a7d20b93] kopya: personel={satir.personel_id} "
            f"tarih={satir.tarih} adet={satir.adet}"
        )
    # (b) Her (personel, tarih) icin EN YENI kayit kalir.
    silinen = baglanti.execute(
        sa.text(
            "DELETE FROM tercih t USING tercih y "
            "WHERE t.personel_id = y.personel_id AND t.tarih = y.tarih "
            "AND t.tercih_id < y.tercih_id RETURNING t.tercih_id"
        )
    ).fetchall()
    print(f"[goc c4f1a7d20b93] silinen kopya satir: {len(silinen)} -> {[s.tercih_id for s in silinen]}")
    # (c) Kisit en sona: temizlik yapilmadan konulursa goc patlardi.
    op.create_unique_constraint("uq_tercih_personel_tarih", "tercih", ["personel_id", "tarih"])


def downgrade() -> None:
    # Silinen kopyalar GERI GELMEZ; downgrade yalniz kisiti kaldirir.
    op.drop_constraint("uq_tercih_personel_tarih", "tercih", type_="unique")
