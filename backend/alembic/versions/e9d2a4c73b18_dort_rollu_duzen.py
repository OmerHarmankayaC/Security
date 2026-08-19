"""rol enum'u dorde cikarildi (SRS 5.10, FR-10.12)

Revision ID: e9d2a4c73b18
Revises: d7b3e5c81f04

MEVCUT SATIRLAR ESLENIR:
    YONETICI -> IDARE               (vardiya planlama yetkileri ayni kaldi)
    YONETIM  -> HESAP_YONETICISI    (hesap yetkileri ayni kaldi)
    CALISAN  -> CALISAN

SISTEM_YONETICISI'NE KIMSE YUKSELTILMEZ. Hangi hesabin sistem yoneticisi
olacagi bir URUN karari; goc bunu tahmin edemez. Yukseltme kurulum betigiyle
yapilir (scripts/yonetim_hesabi_olustur.py, FR-10.10). Goc sonrasi sistemde
sifir sistem yoneticisi bulunur ve bu GECICI olarak dogrudur: FR-10.12'nin
"en az bir etkin sistem yoneticisi" kurali ISLEMLERE uygulanir (son olani
dusurmeyi engeller), veritabani kisiti degildir.

ENUM YERINE YENI TIP: PostgreSQL'de ALTER TYPE ... ADD VALUE islem blogu
icinde kullanilamaz ve RENAME VALUE tek tek yazilsa bile eski/yeni degerin
ayni islemde birlikte gorunmesi gerekir. Yeni tip kurup sutunu USING ile
cevirmek, esleme ile tip degisimini TEK ifadede yapar.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e9d2a4c73b18"
down_revision: str | Sequence[str] | None = "d7b3e5c81f04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_YENI = ("CALISAN", "IDARE", "HESAP_YONETICISI", "SISTEM_YONETICISI")
_ESKI = ("CALISAN", "YONETICI", "YONETIM")


def upgrade() -> None:
    baglanti = op.get_bind()
    sayim = baglanti.execute(
        sa.text("SELECT rol, count(*) FROM kullanici GROUP BY rol ORDER BY rol")
    ).all()
    for rol, adet in sayim:
        print(f"[goc e9d2a4c73b18] eslenecek: {rol} -> {adet} hesap")

    # CHECK KISITI ONCE DUSURULUR. `ck_kullanici_calisan_personele_bagli`
    # ifadesi `rol <> 'CALISAN'::rol` yazar ve sutunun tipi degisirken eski
    # tipe bagli kalir; PostgreSQL "operator does not exist: rol_yeni <> rol"
    # der. Kisit tip degisiminden SONRA yeni tiple yeniden kurulur.
    op.execute(
        sa.text("ALTER TABLE kullanici DROP CONSTRAINT ck_kullanici_calisan_personele_bagli")
    )
    op.execute(sa.text("CREATE TYPE rol_yeni AS ENUM " + str(_YENI)))
    op.execute(
        sa.text(
            "ALTER TABLE kullanici ALTER COLUMN rol TYPE rol_yeni USING CASE rol::text "
            "WHEN 'YONETICI' THEN 'IDARE' "
            "WHEN 'YONETIM' THEN 'HESAP_YONETICISI' "
            "ELSE rol::text END::rol_yeni"
        )
    )
    op.execute(sa.text("DROP TYPE rol"))
    op.execute(sa.text("ALTER TYPE rol_yeni RENAME TO rol"))
    # FR-10.6: personel baglama YALNIZ calisan rolu icin zorunlu; diger uc
    # rol icin istege bagli. Kural degismedi, yalnizca yeni tiple yeniden
    # kuruluyor.
    op.execute(
        sa.text(
            "ALTER TABLE kullanici ADD CONSTRAINT ck_kullanici_calisan_personele_bagli "
            "CHECK (rol <> 'CALISAN'::rol OR personel_id IS NOT NULL)"
        )
    )

    kalan = baglanti.execute(
        sa.text("SELECT count(*) FROM kullanici WHERE rol = 'SISTEM_YONETICISI'")
    ).scalar()
    print(
        f"[goc e9d2a4c73b18] sistem yoneticisi sayisi: {kalan} — "
        "kurulum betigiyle bir hesap yukseltilmeli (FR-10.10)"
    )


def downgrade() -> None:
    # SISTEM_YONETICISI geri eslemede YONETIM olur; ayrim geri alinamaz.
    op.execute(
        sa.text("ALTER TABLE kullanici DROP CONSTRAINT ck_kullanici_calisan_personele_bagli")
    )
    op.execute(sa.text("CREATE TYPE rol_eski AS ENUM " + str(_ESKI)))
    op.execute(
        sa.text(
            "ALTER TABLE kullanici ALTER COLUMN rol TYPE rol_eski USING CASE rol::text "
            "WHEN 'IDARE' THEN 'YONETICI' "
            "WHEN 'HESAP_YONETICISI' THEN 'YONETIM' "
            "WHEN 'SISTEM_YONETICISI' THEN 'YONETIM' "
            "ELSE rol::text END::rol_eski"
        )
    )
    op.execute(sa.text("DROP TYPE rol"))
    op.execute(sa.text("ALTER TYPE rol_eski RENAME TO rol"))
    op.execute(
        sa.text(
            "ALTER TABLE kullanici ADD CONSTRAINT ck_kullanici_calisan_personele_bagli "
            "CHECK (rol <> 'CALISAN'::rol OR personel_id IS NOT NULL)"
        )
    )
