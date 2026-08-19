"""musaitlik_belgesi tablosu — izin kaydina eklenen belge

Revision ID: d7b3e5c81f04
Revises: c4f1a7d20b93
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d7b3e5c81f04"
down_revision: str | Sequence[str] | None = "c4f1a7d20b93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "musaitlik_belgesi",
        sa.Column("belge_id", sa.Integer(), nullable=False),
        sa.Column("musaitlik_id", sa.Integer(), nullable=False),
        sa.Column("dosya_adi", sa.String(), nullable=False),
        sa.Column("icerik_tipi", sa.String(), nullable=False),
        sa.Column("boyut_bayt", sa.Integer(), nullable=False),
        # Icerik VERITABANINDA durur: yedekleme yordami pg_dump'tir ve dosya
        # sistemi ondan haric kalirdi (bkz. modelin docstring'i).
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
        # BIRE BIR: bir izin kaydinin en fazla bir belgesi olur.
        sa.UniqueConstraint("musaitlik_id", name="uq_musaitlik_belgesi_musaitlik"),
    )


def downgrade() -> None:
    op.drop_table("musaitlik_belgesi")
