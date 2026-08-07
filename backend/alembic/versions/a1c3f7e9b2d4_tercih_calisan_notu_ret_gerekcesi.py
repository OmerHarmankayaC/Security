"""tercih calisan_notu ve ret_gerekcesi alanlari

Sprint 3 Gun 13 (Calisan Paneli): calisan_notu, calisanin tercih bildirirken
girdigi gerekce; ret_gerekcesi, yoneticinin ret gerekcesi (FR-3.4), calisana
gosterilir. Ayri alanlar, cunku farkli kisiye ait ve farkli asamada yazilir.

Revision ID: a1c3f7e9b2d4
Revises: b413bb80a4bd
Create Date: 2026-08-07 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1c3f7e9b2d4'
down_revision: Union[str, None] = 'b413bb80a4bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tercih', sa.Column('calisan_notu', sa.String(), nullable=True))
    op.add_column('tercih', sa.Column('ret_gerekcesi', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('tercih', 'ret_gerekcesi')
    op.drop_column('tercih', 'calisan_notu')
