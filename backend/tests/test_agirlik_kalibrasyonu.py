"""Agirlik kalibrasyonu regresyon testi (PROGRESS.md, Ek Gorev - agirlik
kalibrasyonu turu). SRS S1'in "baskin agirlik" ilkesini somutlastirir: w1,
S1 haric butun esnek hedeflerin ulasabildigi agirlikli toplamdan katiyen
buyuk olmalidir - degilse cozucu bir kapsama acigi biriminden vazgecip
diger hedefleri topluca iyilestirerek "kazanabilir" ve S1'in baskinligi
kagit uzerinde kalir (bkz. PROGRESS.md'deki 8450 > w1=1000 bulgusu).

Gercek demo senaryosunu (scripts/demo_veri_uret.uret) uretip her iki
donemi de gercekten cozer; canli PostgreSQL gerektirir.
"""

import sys
from pathlib import Path

from sqlalchemy import select

from app.db import OturumYerel
from app.models.kural import Kural
from app.models.sonuc import CozumIsiDurumu, Donem
from app.repositories.sonuc import CozumIsiDeposu
from app.services.cozum_servisi import CozumServisi
from tests.conftest import isi_calistir_ve_bekle, pg_yoksa_atla

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.demo_veri_uret import _her_seyi_temizle, uret  # noqa: E402


def test_s1_agirligi_diger_hedeflerin_agirlikli_toplamindan_buyuk() -> None:
    pg_yoksa_atla()
    oturum = OturumYerel()
    try:
        # Diger test modullerinin (ornegin test_cozum_servisi.py) benzersiz sonek
        # kullanmayan H1..S8 kural satirlari onceki calistirmalardan kalmis
        # olabilir (bilinen bir test-izolasyon eksigi, bkz. PROGRESS.md Gun 11);
        # uret(sifirla=True) yalnizca "Guvenlik Gorevi" yetkinligi zaten varsa
        # temizler, o yuzden burada kosulsuz temizleniyor.
        _her_seyi_temizle(oturum)
        oturum.commit()
        # coz=False: bu test cozumu KENDISI yurutuyor ve ceza dokumlerini
        # karsilastiriyor. Uretecin ayrica cozmesi hem sureyi ikiye
        # katlar hem de olculecek surumu belirsizlestirirdi.
        uret(sifirla=False, coz=False)
        oturum.commit()
        donemler = oturum.execute(select(Donem).order_by(Donem.donem_id)).scalars().all()
        assert len(donemler) == 6, (
            "demo_veri_uret alti donem uretmeli (Gecen, Bu Hafta, Sikisik, Tatilli, "
            "Fazla Calisma, Kota Siniri). Tur 4'te iki senaryo eklendi: kurallarin "
            "islediginin gorulebilmesi icin fazla calisma ve kota tuketimi gosteren "
            "donemler gerekiyordu."
        )
        # Kalibrasyon iki donem olcer: agirlik dengesi "kadro yeterken acik
        # birakilmamali" (rahat bir hafta) ve "kadro yetmezken acik gorunmeli"
        # (Sikisik) uzerinden tanimli. Donemler tarih sirasinda: Gecen,
        # Bu Hafta, Sikisik, Tatilli. Rahat ornek olarak "Bu Hafta" alinir -
        # izin kaydi tasimayan bir hafta. Tatilli donem resmi tatil
        # cozumlemesini gostermek icin var, agirlik dengesine yeni bir sey
        # soylemez.
        rahat_id, sikisik_id = donemler[1].donem_id, donemler[2].donem_id

        w1 = oturum.execute(select(Kural.agirlik).where(Kural.kimlik == "S1")).scalar_one()

        servis = CozumServisi(oturum)
        # SURE LIMITLERI TUR 5'TE YUKSELTILDI ve nedeni testin konusu DEGIL:
        # saat ekseninde yirmi sekiz gunluk sikisik donem ilk uygun cozume
        # ancak kirk bes saniye civarinda ulasiyor (olcum PROGRESS_V2'de,
        # "K1 tehlikede" basligi altinda). Bu test agirlik dengesini olcer;
        # cozumun ne kadar surdugunu K1 olcer ve o olcum ayri durur.
        is_kaydi_rahat = servis.baslat(rahat_id, zaman_limiti_saniye=90)
        oturum.commit()
        is_kaydi_sikisik = servis.baslat(sikisik_id, zaman_limiti_saniye=180)
        oturum.commit()
        assert is_kaydi_rahat is not None
        assert is_kaydi_sikisik is not None

        durum_rahat = isi_calistir_ve_bekle(is_kaydi_rahat.is_id)
        durum_sikisik = isi_calistir_ve_bekle(is_kaydi_sikisik.is_id)
        assert durum_rahat != CozumIsiDurumu.BASARISIZ
        assert durum_sikisik != CozumIsiDurumu.BASARISIZ

        # Cozum isleri ayri sureclerde/oturumlarda tamamlandi; bu oturumun kendi
        # kimlik haritasi hala cozulmeden onceki (ceza_dokumu=None) kopyalari
        # tutuyor olabilir - taze okumaya zorla.
        oturum.expire_all()

        vakalar = ((is_kaydi_rahat.is_id, "Rahat"), (is_kaydi_sikisik.is_id, "Sikisik"))
        for is_id, donem_adi in vakalar:
            is_kaydi = CozumIsiDeposu(oturum).getir(is_id)
            assert is_kaydi is not None and is_kaydi.ceza_dokumu is not None

            agirliklar = dict(
                oturum.execute(
                    select(Kural.kimlik, Kural.agirlik).where(Kural.aktif.is_(True))
                ).all()
            )
            s1_haric_toplam = sum(
                ham * agirliklar[kimlik]
                for kimlik, ham in is_kaydi.ceza_dokumu.items()
                if kimlik != "S1" and agirliklar.get(kimlik) is not None
            )
            assert w1 > s1_haric_toplam, (
                f"{donem_adi} donemde S1 agirligi ({w1}) S1-haric agirlikli "
                f"toplamdan ({s1_haric_toplam}) buyuk degil - 'baskin agirlik' "
                f"ilkesi (SRS S1) saglanmiyor"
            )
    finally:
        oturum.rollback()
        oturum.close()
