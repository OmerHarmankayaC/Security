"""aktif sutunlarini ayni sozlesmeye getir

NEDEN. `aktif` bayragi bes tanim tablosunda ayni isi yapiyor ama iki farkli
sozlesmeyle duruyordu:

    kural           NOT NULL, sunucu varsayilani YOK
    gorev_noktasi   NOT NULL, sunucu varsayilani YOK
    yetkinlik       NOT NULL, DEFAULT TRUE
    bina            NOT NULL, DEFAULT TRUE
    vardiya_tipi    NOT NULL, DEFAULT TRUE

Ilk ikisi ilk semada (b413bb80a4bd) varsayilansiz olusturulmus, son ucu bu
turda (d5e70a91c26f) varsayilanla eklenmisti. Bugun bu fark bir hataya yol
ACMIYOR: sutunlar NOT NULL oldugu icin varsayilansiz bir INSERT sessizce
`false` uretmez, hata verir. Duzeltilmesinin nedeni baska: ayni isi yapan iki
sutunun iki farkli sozlesmeyle durmasi, birine bakip digeri hakkinda yanlis
varsayim uretmeye davettir. Kural katalogunda S1'in pasif cikmasinin
sorusturulmasi sirasinda "acaba varsayilan mi eksikti" sorusu tam da bu
belirsizlikten dogdu (bkz. PROGRESS.md, S1 pasif sorusturmasi).

Bu goc yalnizca sunucu varsayilanini ekler; MEVCUT SATIRLARI DEGISTIRMEZ.
Pasiflestirilmis bir kural ya da gorev noktasi pasif kalir — varsayilan
yalnizca sonraki INSERT'lerde, `aktif` hic yazilmadiginda devreye girer.

KAPSAM DISI. `personel` bu listede yoktur: aktiflik orada bir bayrakla degil
tarih araligiyla (aktif_baslangic / aktif_bitis) ifade edilir (SDD 4.2.1).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3b81f47a95c"
down_revision: Union[str, None] = "d5e70a91c26f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLOLAR = ("kural", "gorev_noktasi")


def upgrade() -> None:
    for tablo in _TABLOLAR:
        op.alter_column(
            tablo,
            "aktif",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.true(),
        )


def downgrade() -> None:
    for tablo in _TABLOLAR:
        op.alter_column(
            tablo,
            "aktif",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )
