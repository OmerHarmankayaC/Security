"""kural katalogu saatlik duzene: H5 yeniden, H9/H10/S1f eklendi

Revision ID: e7b2c4915d80
Revises: d1f83a6c40b2
Create Date: 2026-08-13

Tur 4. SEMA DEGISMEZ; degisen KURAL KAYITLARIDIR (`kural` tablosu, SDD
4.2.3). Uc is birden yapilir:

1. **H5'in parametresi tasinir.** `azami_haftalik_saat` -> `haftalik_mutlak_tavan`
   ve degeri 66'ya cekilir. Kirk bes saat artik tavan degil, fazla
   calismanin basladigi ESIKTIR (H10'un parametresi). Anahtar
   degistirilmeden birakilsaydi H5 parametresini bulamayip KeyError ile
   duserdi; degeri 45'te birakilsaydi H10 ile H5 ayni sayiyi iki farkli
   anlamda tasirdi.

2. **H9 ve H10 eklenir.** Katalogda satiri bulunmayan bir kural
   `kurallari_yukle` tarafindan HIC kurulmaz - sinif kayitli olsa bile
   modele girmez. Yeni kurallar bu yuzden veri olarak da eklenmelidir.

3. **S1f eklenir** (fazla kadro cezasi, `w1f = 2`). S6/S6b'deki ayni
   bolme: kural tablosu kural basina tek agirlik sutunu tasir, S1'in
   formulasyonunda iki agirlik vardir.

Geri alma her uc adimi da tersine cevirir ve VERI KAYBETMEZ: H5'in
parametresi eski adiyla ve eski degeriyle geri yazilir, eklenen uc satir
silinir.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7b2c4915d80"
down_revision: str | Sequence[str] | None = "d1f83a6c40b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# SRS 3.3.5. Deger olarak burada duruyorlar cunku goc, uygulamanin kural
# siniflarini ITHAL ETMEZ: goc dosyasi semanin o andaki halini yansitir ve
# kodun ilerideki hali onu degistirmemelidir.
_H5_ESKI_ANAHTAR = "azami_haftalik_saat"
_H5_YENI_ANAHTAR = "haftalik_mutlak_tavan"
_H5_YENI_DEGER = 66
_H5_ESKI_DEGER = 45

_YENI_KURALLAR: tuple[tuple[str, str, str, int | None], ...] = (
    # (kimlik, tip, parametreler_json, agirlik)
    ("H9", "ZORUNLU", '{"azami_gunluk_saat": 11}', None),
    ("H10", "ZORUNLU", '{"fazla_calisma_esigi": 45, "yillik_fazla_kotasi": 270}', None),
    # w1f = 2 (K4 baslangic degeri). Kesin olan `w1f << w1` bagintisidir;
    # kalibrasyon Tur 8'in isi.
    ("S1f", "ESNEK", "{}", 2),
)


def upgrade() -> None:
    baglanti = op.get_bind()

    # 1. H5'in parametresi: anahtar degisir, deger 66 olur.
    baglanti.execute(
        sa.text(
            """
            UPDATE kural
               SET parametreler = (parametreler - :eski)
                                  || jsonb_build_object(CAST(:yeni AS text), CAST(:deger AS int))
             WHERE kimlik = 'H5'
            """
        ),
        {"eski": _H5_ESKI_ANAHTAR, "yeni": _H5_YENI_ANAHTAR, "deger": _H5_YENI_DEGER},
    )

    # 2-3. Yeni kural satirlari. Kayit zaten varsa dokunulmaz: goc iki kez
    # kosulabilir olmali ve kullanicinin degistirdigi bir agirligi geri
    # almamali.
    for kimlik, tip, parametreler, agirlik in _YENI_KURALLAR:
        baglanti.execute(
            sa.text(
                """
                INSERT INTO kural (kimlik, tip, parametreler, agirlik, aktif)
                SELECT CAST(:kimlik AS varchar), CAST(:tip AS kuraltipi),
                       CAST(:parametreler AS jsonb), CAST(:agirlik AS int), TRUE
                 WHERE NOT EXISTS (SELECT 1 FROM kural WHERE kimlik = :kimlik)
                """
            ),
            {"kimlik": kimlik, "tip": tip, "parametreler": parametreler, "agirlik": agirlik},
        )


def downgrade() -> None:
    baglanti = op.get_bind()

    baglanti.execute(
        sa.text("DELETE FROM kural WHERE kimlik IN ('H9', 'H10', 'S1f')"),
    )
    baglanti.execute(
        sa.text(
            """
            UPDATE kural
               SET parametreler = (parametreler - :yeni)
                                  || jsonb_build_object(CAST(:eski AS text), CAST(:deger AS int))
             WHERE kimlik = 'H5'
            """
        ),
        {"eski": _H5_ESKI_ANAHTAR, "yeni": _H5_YENI_ANAHTAR, "deger": _H5_ESKI_DEGER},
    )
