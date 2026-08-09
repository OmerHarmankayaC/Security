"""yetkinlik, bina ve vardiya tipine aktif bayragi

Silme davranisinin gereksinimi (madde 1): kullanimda olan bir tanim
SILINMEZ, pasiflestirilir. Gecmis cizelgeler tanim satirlarina yabanci
anahtarla baglidir (SDD 4.1); satir gidince yayinlanmis bir donemin
atamalari okunamaz hale gelir.

`gorev_noktasi` bu bayragi zaten tasiyordu (SDD 4.2.1). Ayni davranisin
yetkinlik, bina ve vardiya_tipi icin de tanimlanabilmesi bu uc sutunu
gerektiriyor. `personel` disarida kalir: aktiflik orada tarih araligiyla
(aktif_baslangic / aktif_bitis) ifade edilir ve ikinci bir bayrak ayni
bilginin iki kaynaga ayrismasi olurdu.

MEVCUT VERI. Bugune kadarki butun tanimlar aktiftir; sutun NOT NULL ve
sunucu varsayilani TRUE ile eklenir, boylece var olan satirlar tek
adimda dogru degeri alir. server_default kalicidir: dogrudan SQL ile
satir ekleyen betikler (demo veri ureteci disinda) bayragi atlarsa
tanim sessizce pasif dogmamalidir.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e70a91c26f"
down_revision: Union[str, None] = "c8f2d1a45b73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLOLAR = ("yetkinlik", "bina", "vardiya_tipi")


def upgrade() -> None:
    for tablo in _TABLOLAR:
        op.add_column(
            tablo,
            sa.Column("aktif", sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def downgrade() -> None:
    for tablo in _TABLOLAR:
        op.drop_column(tablo, "aktif")
