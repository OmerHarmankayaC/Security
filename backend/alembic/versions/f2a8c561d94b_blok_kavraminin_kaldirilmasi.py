"""blok kavraminin kaldirilmasi: atama blok kaydina, vardiya_tipi duser

Revision ID: f2a8c561d94b
Revises: e7b2c4915d80
Create Date: 2026-08-13

Tur 5 Is 2 (SDD 4.2.1, SRS 3.3.2-3.3.4, TD-13). Calisma zamani artik onceden
tanimli bloklarin secimi degil, saatin kendisi uzerinden kurulur: baslangic
saati ve sure COZUMUN CIKTISIDIR. Blok kataloguna bagli her sey bu gocte
duser.

Yapilan alti is:

1. **`atama` blok kaydina donusur.** `tarih` + `vardiya_tipi_id` yerine
   `baslangic_zamani` + `bitis_zamani` (timestamptz). Mevcut atamalar
   DONUSTURULUR: bagli oldugu vardiya tipinin baslangic ve bitis saatleri
   atamanin tarihiyle birlestirilir, gece yarisini asan tiplerde bitis
   ertesi gune duser.

2. **Donusum SAYILARAK dogrulanir.** Satir sayisi ve toplam kisi-saat,
   donusum oncesi ve sonrasi esit olmak zorundadir; esit degilse goc hata
   verip durur. Sessizce yarim donusen bir cizelge, farki ancak aylar sonra
   bir kapsama raporunda gosterirdi.

3. **Benzersizlik kisiti** `(surum_id, personel_id, tarih)` yerine
   `(surum_id, personel_id, baslangic_zamani)`. DIKKAT — bu bir GUVENCE
   KAYBIDIR: eski anahtar "gunde tek atama"yi veritabani duzeyinde
   zorluyordu, yenisi yalnizca birebir ayni ani yakalar. Ayni gunde farkli
   saatte baslayan ikinci bir blok artik UYGULAMA KATMANINDA durdurulur
   (H1, SDD 4.2.1) ve manuel duzenleme yolunun testi bunu bekler.

4. **`personel.sabit_vardiya_tipi_id` duser.** Sabit vardiya, secilecek bir
   blok bulundugu surece anlamliydi.

5. **`tercih` zaman araligina gecer** (SRS FR-3.2, TD-12). Tercih tipi artik
   "calismama" veya "zaman araligi tercihi"; istenen tip yerine istenen
   ARALIK saklanir.

6. **`vardiya_tipi` tablosu duser** (atama, personel ve tercih baglari
   koptuktan sonra) ve kural kayitlarina iki parametre eklenir:
   `asgari_blok_saat` = 4 (H1) ve `gece_esigi_saat` = 4 (H3). Ikisi de
   SRS 3.3.5'te tanimli ve Kural ekranindan degistirilebilir.

## Geri alma

Yazildi ve denendi. Blok katalogu VERIDEN yeniden turetilir: atamalarda fiilen
gecen (baslangic saati, bitis saati) ciftleri distinct alinip `vardiya_tipi`
satirlarina cevrilir, atamalar o satirlara baglanir. Toplam kisi-saat korunur.
Kataloglarin ADLARI kaybolur ("08.00-16.00" bicimiyle yeniden uretilir) —
geri alma veriyi degil ADLANDIRMAYI kaybeder ve bu kabul edilmistir; blok
adinin kendisi hicbir kural kararina girmiyordu.

On bir saati asan bir blok geri alinamaz gibi gorunebilir (FR-1.3'un azami
sure kisiti) ama o kisit GIRIS dogrulamasidir, sema kisiti degil; goc
tablodaki satiri yazar ve kullanici blogu ekranda gordugunde duzeltir.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2a8c561d94b"
down_revision: str | Sequence[str] | None = "e7b2c4915d80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# SRS 3.3.5. Deger olarak burada duruyorlar cunku goc uygulamanin kural
# siniflarini ITHAL ETMEZ: goc dosyasi semanin o andaki halini yansitir.
_H1_ASGARI_BLOK_SAAT = 4
_H3_GECE_ESIGI_SAAT = 4

# Donusumun iki tarafinda da AYNI sekilde olculen kisi-saat. Zaman damgalari
# timestamptz'dir; fark yerel saate geri cevrilerek alinir, boylece yaz saati
# uygulayan bir sunucuda gece yarisini asan bir blok 23 veya 25 saat gorunup
# dogrulamayi bosuna dusurmez. Olculen sey duvar saati suresidir — donusumun
# yazdigi sey de odur.
_SONRAKI_KISI_SAAT = """
    SELECT COUNT(*),
           COALESCE(SUM(EXTRACT(EPOCH FROM (
               (bitis_zamani AT TIME ZONE current_setting('TimeZone'))
             - (baslangic_zamani AT TIME ZONE current_setting('TimeZone'))
           )) / 3600.0), 0)
      FROM atama
"""

_ONCEKI_KISI_SAAT = """
    SELECT COUNT(*), COALESCE(SUM(vt.sure_saat), 0)
      FROM atama a
      JOIN vardiya_tipi vt ON vt.vardiya_tipi_id = a.vardiya_tipi_id
"""


def _dogrula(baglanti: sa.Connection, onceki: tuple[int, float]) -> None:
    sonraki_satir, sonraki_saat = baglanti.execute(sa.text(_SONRAKI_KISI_SAAT)).one()
    onceki_satir, onceki_saat = onceki
    if int(sonraki_satir) != int(onceki_satir) or abs(
        float(sonraki_saat) - float(onceki_saat)
    ) > 1e-6:
        raise RuntimeError(
            "Atama donusumu dogrulanamadi: "
            f"once {onceki_satir} satir / {float(onceki_saat):.2f} kisi-saat, "
            f"sonra {sonraki_satir} satir / {float(sonraki_saat):.2f} kisi-saat. "
            "Goc geri alindi."
        )


def upgrade() -> None:
    baglanti = op.get_bind()
    onceki = baglanti.execute(sa.text(_ONCEKI_KISI_SAAT)).one()

    # --- 1. atama: blok kaydi -------------------------------------------
    op.add_column("atama", sa.Column("baslangic_zamani", sa.DateTime(timezone=True), nullable=True))
    op.add_column("atama", sa.Column("bitis_zamani", sa.DateTime(timezone=True), nullable=True))
    baglanti.execute(
        sa.text(
            """
            UPDATE atama a
               SET baslangic_zamani = (a.tarih + vt.baslangic_saati),
                   bitis_zamani     = (a.tarih + vt.bitis_saati)
                                    + CASE WHEN vt.bitis_saati <= vt.baslangic_saati
                                           THEN INTERVAL '1 day' ELSE INTERVAL '0' END
              FROM vardiya_tipi vt
             WHERE vt.vardiya_tipi_id = a.vardiya_tipi_id
            """
        )
    )
    # Bagli vardiya tipi bulunamayan bir atama donusemez; bu bir yabanci
    # anahtar ihlali olurdu ve sema onu zaten disliyor, ama sessiz NULL
    # birakmaktansa burada durmak dogru.
    donusemeyen = baglanti.execute(
        sa.text("SELECT COUNT(*) FROM atama WHERE baslangic_zamani IS NULL")
    ).scalar_one()
    if donusemeyen:
        raise RuntimeError(f"{donusemeyen} atama vardiya tipine baglanamadi; goc geri alindi.")

    op.alter_column("atama", "baslangic_zamani", nullable=False)
    op.alter_column("atama", "bitis_zamani", nullable=False)
    _dogrula(baglanti, onceki)

    op.drop_constraint("uq_atama_surum_personel_tarih", "atama", type_="unique")
    op.drop_column("atama", "tarih")
    op.drop_column("atama", "vardiya_tipi_id")
    op.create_unique_constraint(
        "uq_atama_surum_personel_baslangic",
        "atama",
        ["surum_id", "personel_id", "baslangic_zamani"],
    )

    # --- 2. personel: sabit vardiya duser --------------------------------
    op.drop_column("personel", "sabit_vardiya_tipi_id")

    # --- 3. tercih: zaman araligina --------------------------------------
    op.add_column("tercih", sa.Column("tercih_baslangic", sa.Time(), nullable=True))
    op.add_column("tercih", sa.Column("tercih_bitis", sa.Time(), nullable=True))
    baglanti.execute(
        sa.text(
            """
            UPDATE tercih t
               SET tercih_baslangic = vt.baslangic_saati,
                   tercih_bitis     = vt.bitis_saati
              FROM vardiya_tipi vt
             WHERE vt.vardiya_tipi_id = t.vardiya_tipi_id
            """
        )
    )
    op.drop_column("tercih", "vardiya_tipi_id")
    # Enum degeri YENIDEN ADLANDIRILIR, yeni bir tip yaratilmaz: mevcut
    # satirlar degeri tasimaya devam eder ve donusum kaybi olmaz.
    op.execute("ALTER TYPE tercihtipi RENAME VALUE 'VARDIYA_TIPI_TERCIHI' TO 'ZAMAN_ARALIGI_TERCIHI'")

    # --- 4. vardiya_tipi duser -------------------------------------------
    op.drop_table("vardiya_tipi")

    # --- 5. kural parametreleri ------------------------------------------
    # `||` var olan anahtari ezer; kullanicinin degistirdigi bir degeri geri
    # almamak icin yalnizca ANAHTAR YOKSA yazilir.
    for kimlik, anahtar, deger in (
        ("H1", "asgari_blok_saat", _H1_ASGARI_BLOK_SAAT),
        ("H3", "gece_esigi_saat", _H3_GECE_ESIGI_SAAT),
    ):
        baglanti.execute(
            sa.text(
                """
                UPDATE kural
                   SET parametreler = parametreler
                        || jsonb_build_object(CAST(:anahtar AS text), CAST(:deger AS int))
                 WHERE kimlik = :kimlik
                   AND NOT (parametreler ? CAST(:anahtar AS text))
                """
            ),
            {"kimlik": kimlik, "anahtar": anahtar, "deger": deger},
        )


def downgrade() -> None:
    baglanti = op.get_bind()
    onceki_satir, onceki_saat = baglanti.execute(sa.text(_SONRAKI_KISI_SAAT)).one()

    op.execute("ALTER TYPE tercihtipi RENAME VALUE 'ZAMAN_ARALIGI_TERCIHI' TO 'VARDIYA_TIPI_TERCIHI'")

    op.create_table(
        "vardiya_tipi",
        sa.Column("vardiya_tipi_id", sa.Integer(), primary_key=True),
        sa.Column("ad", sa.String(), nullable=False),
        sa.Column("baslangic_saati", sa.Time(), nullable=False),
        sa.Column("bitis_saati", sa.Time(), nullable=False),
        sa.Column("sure_saat", sa.Numeric(4, 2), nullable=False),
        sa.Column("gece_mi", sa.Boolean(), nullable=False),
        sa.Column("aktif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("olusturma_zamani", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("guncelleme_zamani", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Katalog VERIDEN turetilir: atamalarda fiilen gecen (baslangic, bitis)
    # ciftleri. `gece_mi` bayragi da geri gelirken hesaplanir - bir blok gece
    # donemiyle (20.00-06.00) kesisiyorsa gece isaretlenir. Bayragin kendisi
    # yukari yonde kalkti; burada yalnizca eski semanin NOT NULL sutununu
    # doldurmak icin var.
    baglanti.execute(
        sa.text(
            """
            INSERT INTO vardiya_tipi (ad, baslangic_saati, bitis_saati, sure_saat, gece_mi)
            SELECT to_char(bas, 'HH24.MI') || '-' || to_char(bit, 'HH24.MI'),
                   bas, bit, sure,
                   (bas >= TIME '20:00' OR bas < TIME '06:00' OR bit > TIME '20:00'
                    OR bit <= TIME '06:00')
              FROM (
                    SELECT DISTINCT
                           (baslangic_zamani AT TIME ZONE current_setting('TimeZone'))::time AS bas,
                           (bitis_zamani     AT TIME ZONE current_setting('TimeZone'))::time AS bit,
                           EXTRACT(EPOCH FROM (
                               (bitis_zamani     AT TIME ZONE current_setting('TimeZone'))
                             - (baslangic_zamani AT TIME ZONE current_setting('TimeZone'))
                           )) / 3600.0 AS sure
                      FROM atama
                   ) AS bloklar
            """
        )
    )

    op.add_column("tercih", sa.Column("vardiya_tipi_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "tercih_vardiya_tipi_id_fkey",
        "tercih",
        "vardiya_tipi",
        ["vardiya_tipi_id"],
        ["vardiya_tipi_id"],
    )
    baglanti.execute(
        sa.text(
            """
            UPDATE tercih t
               SET vardiya_tipi_id = vt.vardiya_tipi_id
              FROM vardiya_tipi vt
             WHERE vt.baslangic_saati = t.tercih_baslangic
               AND vt.bitis_saati = t.tercih_bitis
            """
        )
    )
    op.drop_column("tercih", "tercih_bitis")
    op.drop_column("tercih", "tercih_baslangic")

    op.add_column("personel", sa.Column("sabit_vardiya_tipi_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "personel_sabit_vardiya_tipi_id_fkey",
        "personel",
        "vardiya_tipi",
        ["sabit_vardiya_tipi_id"],
        ["vardiya_tipi_id"],
    )

    op.add_column("atama", sa.Column("tarih", sa.Date(), nullable=True))
    op.add_column("atama", sa.Column("vardiya_tipi_id", sa.Integer(), nullable=True))
    baglanti.execute(
        sa.text(
            """
            UPDATE atama a
               SET tarih = (a.baslangic_zamani AT TIME ZONE current_setting('TimeZone'))::date,
                   vardiya_tipi_id = vt.vardiya_tipi_id
              FROM vardiya_tipi vt
             WHERE vt.baslangic_saati =
                   (a.baslangic_zamani AT TIME ZONE current_setting('TimeZone'))::time
               AND vt.bitis_saati =
                   (a.bitis_zamani AT TIME ZONE current_setting('TimeZone'))::time
            """
        )
    )
    baglanmayan = baglanti.execute(
        sa.text("SELECT COUNT(*) FROM atama WHERE vardiya_tipi_id IS NULL")
    ).scalar_one()
    if baglanmayan:
        raise RuntimeError(f"{baglanmayan} atama turetilen kataloga baglanamadi; geri alma durdu.")

    op.alter_column("atama", "tarih", nullable=False)
    op.alter_column("atama", "vardiya_tipi_id", nullable=False)
    op.create_foreign_key(
        "atama_vardiya_tipi_id_fkey",
        "atama",
        "vardiya_tipi",
        ["vardiya_tipi_id"],
        ["vardiya_tipi_id"],
    )

    sonraki_satir, sonraki_saat = baglanti.execute(sa.text(_ONCEKI_KISI_SAAT)).one()
    if int(sonraki_satir) != int(onceki_satir) or abs(
        float(sonraki_saat) - float(onceki_saat)
    ) > 1e-6:
        raise RuntimeError(
            "Geri alma dogrulanamadi: "
            f"once {onceki_satir} satir / {float(onceki_saat):.2f} kisi-saat, "
            f"sonra {sonraki_satir} satir / {float(sonraki_saat):.2f} kisi-saat."
        )

    op.drop_constraint("uq_atama_surum_personel_baslangic", "atama", type_="unique")
    op.drop_column("atama", "bitis_zamani")
    op.drop_column("atama", "baslangic_zamani")
    op.create_unique_constraint(
        "uq_atama_surum_personel_tarih", "atama", ["surum_id", "personel_id", "tarih"]
    )

    for kimlik, anahtar in (("H1", "asgari_blok_saat"), ("H3", "gece_esigi_saat")):
        baglanti.execute(
            sa.text(
                "UPDATE kural SET parametreler = parametreler - CAST(:anahtar AS text) "
                "WHERE kimlik = :kimlik"
            ),
            {"kimlik": kimlik, "anahtar": anahtar},
        )
