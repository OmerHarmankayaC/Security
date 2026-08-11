"""SDD 5.3 FONKSIYON model_kur()'un birebir uygulamasi.

Model kurucu, kural katalogunu CP-SAT modeline donusturur. Kurallarin
kendisi modele nasil ekleneceklerini bildigi icin bu fonksiyon kural
tiplerinden habersizdir; yalnizca karar degiskenlerini olusturur ve
kurallara sirayla devreder.
"""

from datetime import date

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.temel import Kural, XAnahtari


def model_kur(
    baglam: Baglam,
    zaman_ekseni: list[date],
    kurallar: list[Kural],
    isitma_penceresi_atamalari: list[AtamaKaydi] | None = None,
    kilitli_atamalar: list[AtamaKaydi] | None = None,
    cozum_ipucu: list[AtamaKaydi] | None = None,
) -> tuple[
    cp_model.CpModel, dict[XAnahtari, cp_model.IntVar], Baglam, dict[str, cp_model.LinearExprT]
]:
    """SDD 5.3: model, x <- model_kur(donem, tanimlar, kurallar, isitma_penceresi).

    zaman_ekseni, isitma penceresi + donem gunlerinin ardisik takvim
    gunlerinden olusan birlesik listesidir (caller'in sorumlulugu, SDD
    TD-5). baglam onceden tanim/girdi/talep verisiyle kurulmus olmali;
    bu fonksiyon onun uzerine zaman_ekseni ve y alanlarini doldurur.

    kilitli_atamalar (SDD 5.6, yeniden_coz): yeniden cozumde kullanicinin
    kilitledigi onceki atamalar - isitma penceresiyle ayni mekanizmayla
    (x=1'e sabitlenerek) modele islenir, ama farkli bir nedenden (kullanici
    tercihi, gecmis bir zorunluluk degil) ayri bir parametre olarak tutulur.

    cozum_ipucu (SDD 5.4.1, "devam et"): durdurulan bir isten devralinan
    cozum. Sabitleme DEGILDIR - cozucuye nereden baslayacagini soyler.

    Dorduncu donus degeri, esnek hedeflerin (agirliksiz) ceza ifadelerini
    kural kimligine gore tasir; SDD 5.4'teki 'cozum.hedef_bazinda_ceza()'
    icin cozumden sonra CozucuAdaptoru'na verilir.
    """
    model = cp_model.CpModel()
    baglam.zaman_ekseni = list(zaman_ekseni)

    x: dict[XAnahtari, cp_model.IntVar] = {}
    for p in baglam.personel:
        for g in zaman_ekseni:
            for v in baglam.vardiya_tipleri:
                for n, nokta in baglam.gorev_noktalari.items():
                    if baglam.gereken_sayi(g, v, n) == 0:
                        continue
                    if nokta.onkosul_yetkinlik_id is not None and not baglam.yetkin_mi(
                        p, nokta.onkosul_yetkinlik_id
                    ):
                        continue
                    if not baglam.musait_mi(AtamaKaydi(p, g, v, n)):
                        continue
                    x[(p, g, v, n)] = model.new_bool_var(f"x_p{p}_g{g}_v{v}_n{n}")

    sabit_kumesi = {
        (a.personel_id, a.tarih, a.vardiya_tipi_id, a.nokta_id)
        for a in (isitma_penceresi_atamalari or []) + (kilitli_atamalar or [])
    }
    for anahtar in sabit_kumesi:
        if anahtar in x:
            model.add(x[anahtar] == 1)
        # Anahtar x'te yoksa (ör. talep artik sifir), isitma penceresi/kilitli
        # atama listesindeki bu atama icin zaten sabitlenecek bir karar
        # degiskeni yok demektir; sessizce atlanir.

    # SDD 5.4.1 "devam et": durdurulan isin bulundugu cozum, yeni aramanin
    # BASLANGIC IPUCUDUR. Kisit degil ipucudur - cozucu onu tutmak zorunda
    # degil, ama oradan basladigi icin sonuc ipucundan kotu olmaz.
    # Sabitlenmis anahtarlar disarida birakilir: onlar zaten x == 1.
    for atama in cozum_ipucu or []:
        anahtar = (atama.personel_id, atama.tarih, atama.vardiya_tipi_id, atama.nokta_id)
        if anahtar in x and anahtar not in sabit_kumesi:
            model.add_hint(x[anahtar], 1)

    y: dict[tuple[int, date, int], cp_model.LinearExprT] = {}
    for p in baglam.personel:
        for g in zaman_ekseni:
            for v in baglam.vardiya_tipleri:
                ilgili = [x[(p, g, v, n)] for n in baglam.gorev_noktalari if (p, g, v, n) in x]
                y[(p, g, v)] = sum(ilgili) if ilgili else 0
    baglam.y = y

    ceza_terimleri = []
    ham_terimler: dict[str, cp_model.LinearExprT] = {}
    for kural in kurallar:
        terim = kural.modele_ekle(model, x, baglam)
        if terim is not None:
            ham_terimler[kural.kimlik] = terim
            ceza_terimleri.append(kural.agirlik * terim)
    model.minimize(sum(ceza_terimleri) if ceza_terimleri else 0)

    return model, x, baglam, ham_terimler
