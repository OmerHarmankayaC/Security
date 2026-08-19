"""izin belgesi musaitlik satirina tasindi (SDD 4.2.1, 5.10)

Revision ID: f4a8c1e60d92
Revises: e9d2a4c73b18

AYRI TABLODAN SUTUNA. Belge once `musaitlik_belgesi` adinda bire bir bagli
ayri bir tabloda tutuluyordu; SDD 4.2.1 onu `musaitlik` satirinin icinde
tanimliyor. Ayrimin pratik karsiligi silme davranisidir: sutun oldugunda
kayit silindiginde belge AYNI ISLEMDE gider ve yetim satir ihtimali
tanimsizlasir (SDD 5.10). Ayri tabloda bu, yabanci anahtarin ON DELETE
CASCADE'ine baglidir - dogru kurulmus olsa bile bir kural degil bir ayar.

VERI TASINIR, ATILMAZ: mevcut belgeler yeni sutunlara kopyalanir.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f4a8c1e60d92"
down_revision: str | Sequence[str] | None = "e9d2a4c73b18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("musaitlik", sa.Column("belge_adi", sa.String(), nullable=True))
    op.add_column("musaitlik", sa.Column("belge_tipi", sa.String(), nullable=True))
    op.add_column("musaitlik", sa.Column("belge_boyut", sa.Integer(), nullable=True))
    op.add_column("musaitlik", sa.Column("belge_icerik", sa.LargeBinary(), nullable=True))

    baglanti = op.get_bind()
    tasinan = baglanti.execute(
        sa.text(
            "UPDATE musaitlik m SET belge_adi = b.dosya_adi, belge_tipi = b.icerik_tipi, "
            "belge_boyut = b.boyut_bayt, belge_icerik = b.icerik "
            "FROM musaitlik_belgesi b WHERE b.musaitlik_id = m.musaitlik_id "
            "RETURNING m.musaitlik_id"
        )
    ).fetchall()
    print(f"[goc f4a8c1e60d92] satira tasinan belge: {len(tasinan)}")

    op.drop_table("musaitlik_belgesi")


def downgrade() -> None:
    op.create_table(
        "musaitlik_belgesi",
        sa.Column("belge_id", sa.Integer(), nullable=False),
        sa.Column("musaitlik_id", sa.Integer(), nullable=False),
        sa.Column("dosya_adi", sa.String(), nullable=False),
        sa.Column("icerik_tipi", sa.String(), nullable=False),
        sa.Column("boyut_bayt", sa.Integer(), nullable=False),
        sa.Column("icerik", sa.LargeBinary(), nullable=False),
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
        sa.ForeignKeyConstraint(["musaitlik_id"], ["musaitlik.musaitlik_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("belge_id"),
        sa.UniqueConstraint("musaitlik_id", name="uq_musaitlik_belgesi_musaitlik"),
    )
    op.execute(
        sa.text(
            "INSERT INTO musaitlik_belgesi (musaitlik_id, dosya_adi, icerik_tipi, boyut_bayt, icerik) "
            "SELECT musaitlik_id, belge_adi, belge_tipi, belge_boyut, belge_icerik "
            "FROM musaitlik WHERE belge_icerik IS NOT NULL"
        )
    )
    for sutun in ("belge_icerik", "belge_boyut", "belge_tipi", "belge_adi"):
        op.drop_column("musaitlik", sutun)
