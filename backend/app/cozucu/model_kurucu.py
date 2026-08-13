"""SDD 5.3 FONKSIYON model_kur()'un birebir uygulamasi.

Model kurucu, kural katalogunu CP-SAT modeline donusturur. Kurallarin
kendisi modele nasil ekleneceklerini bildigi icin bu fonksiyon kural
tiplerinden habersizdir; yalnizca karar degiskenlerini olusturur ve
kurallara sirayla devreder.

## Karar degiskeni MUTLAK SAAT EKSENINDEDIR (SRS TD-13)

```
z[p,s] ∈ {0,1}    p personeli s saatinde calisiyor
x[p,s,n] ∈ {0,1}  … ve n gorev noktasinda
Σ_n x[p,s,n] = z[p,s]
```

Eksen donemin basindan itibaren saat sayar ve GUN BASINA SIFIRLANMAZ; gun
kavrami yalnizca sayim icin kullanilir. Gun x saat bicimde kurulan bir
eksende gece yarisini asan bir calisma gunun sonunda kesilir ve
kesintisizlik kisiti onu iki ayri blok sayar - kural, izin verilmesi gereken
calismayi yasaklamis olur.

## Degisken eleme, arama uzayini belirleyen asil yerdir

Musait olmayan saat, on kosulu tasinmayan nokta ve talebin sifir oldugu
saat-nokta cifti icin degisken HIC olusturulmaz. Olusturup sonra sifira
sabitlemek ayni sonucu verir fakat modeli gereksiz buyutur. Bu eleme,
H7 ve H8 kisitlarinin modele ayrica eklenmesine de gerek birakmaz.
"""

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.kurallar.baglam import AtamaKaydi, Baglam
from app.kurallar.temel import Kural, XAnahtari
from app.kurallar.zaman_araligi import ardisik_saatleri_grupla


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
    gunlerinden olusan birlesik listesidir (caller'in sorumlulugu, TD-5).
    baglam onceden tanim/girdi/talep verisiyle kurulmus olmali; bu fonksiyon
    onun uzerine zaman_ekseni, z, bas ve devir alanlarini doldurur.

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

    z: dict[tuple[int, int], cp_model.IntVar] = {}
    x: dict[XAnahtari, cp_model.IntVar] = {}
    for p in baglam.personel:
        for s in baglam.saat_ekseni:
            an = baglam.saat_zamani(s)
            if not baglam.musait_mi(p, an):
                continue
            ulasilabilir = [
                n
                for n in baglam.gorev_noktalari
                if baglam.erisebilir_mi(p, n)
                and baglam.gereken_sayi_saat(an.date(), an.hour, n) > 0
            ]
            if not ulasilabilir:
                continue
            z[(p, s)] = model.new_bool_var(f"z_p{p}_s{s}")
            for n in ulasilabilir:
                x[(p, s, n)] = model.new_bool_var(f"x_p{p}_s{s}_n{n}")
            model.add(sum(x[(p, s, n)] for n in ulasilabilir) == z[(p, s)])
    baglam.z = z

    # --- Blok baslangici gostergesi (SRS H1) -----------------------------
    # bas[p,s] ≥ z[p,s] − z[p,s−1] ;  bas ≤ z[p,s] ;  bas ≤ 1 − z[p,s−1]
    bas: dict[tuple[int, int], cp_model.IntVar] = {}
    for p, s in z:
        gosterge = model.new_bool_var(f"bas_p{p}_s{s}")
        onceki = baglam.zv(p, s - 1) if s > 0 else 0
        model.add(gosterge >= z[(p, s)] - onceki)
        model.add(gosterge <= z[(p, s)])
        model.add(gosterge <= 1 - onceki)
        bas[(p, s)] = gosterge
    baglam.bas = bas

    # --- Devralma gostergesi (SRS TD-1) ----------------------------------
    # devir[p,s] = "s saati calisiliyor VE onceki gunde baslamis bir bloga
    # ait". Gunun ilk saatinde: calisiliyor ama baslangic degilse
    # devralinmistir. Sonraki saatlerde: bir onceki saat devralinmissa ve bu
    # saat de calisiliyorsa ayni blogun parcasidir (araya baslangic giremez,
    # cunku z[s−1] = 1 iken bas[s] = 0'dir).
    #
    # BU GOSTERGE OLMADAN gun basina toplamlar DUVAR SAATINE duser ve iki
    # kural birden bozulur: H9 on iki saatlik bir blogu 4 + 8 diye gorup
    # gecirir, H1'in asgari suresi ise aksam baslangiclarini yasaklar.
    devir: dict[tuple[int, int], cp_model.IntVar] = {}
    for p in baglam.personel:
        for s in baglam.saat_ekseni:
            if (p, s) not in z:
                continue
            gosterge = model.new_bool_var(f"devir_p{p}_s{s}")
            if baglam.gun_saati(s) == 0:
                model.add(gosterge == z[(p, s)] - bas[(p, s)])
            else:
                onceki = devir.get((p, s - 1), 0)
                model.add(gosterge <= onceki)
                model.add(gosterge <= z[(p, s)])
                model.add(gosterge >= onceki + z[(p, s)] - 1)
            devir[(p, s)] = gosterge
    baglam.devir = devir

    # --- Nokta sabitligi (SRS H1) ----------------------------------------
    # x[p,s,n] ≥ z[p,s] + x[p,s−1,n] − 1: personel calismaya devam ettigi
    # surece gorev noktasi degismez.
    for p, s, n in x:
        onceki = x.get((p, s - 1, n))
        if onceki is not None:
            model.add(x[(p, s, n)] >= z[(p, s)] + onceki - 1)

    # --- Isitma penceresi ve kilitli atamalar sabitlenir (TD-5) ----------
    sabit_kumesi: set[XAnahtari] = set()
    for atama in (isitma_penceresi_atamalari or []) + (kilitli_atamalar or []):
        for an in atama.saatler():
            s = baglam.saat_indeksi(an)
            if s is not None:
                sabit_kumesi.add((atama.personel_id, s, atama.nokta_id))
    for anahtar in sabit_kumesi:
        if anahtar in x:
            model.add(x[anahtar] == 1)
        # Anahtar x'te yoksa (ör. talep artik sifir) sabitlenecek bir karar
        # degiskeni yok demektir; sessizce atlanir.

    # SDD 5.4.1 "devam et": durdurulan isin bulundugu cozum, yeni aramanin
    # BASLANGIC IPUCUDUR. Kisit degil ipucudur - cozucu onu tutmak zorunda
    # degil, ama oradan basladigi icin sonuc ipucundan kotu olmaz.
    for atama in cozum_ipucu or []:
        for an in atama.saatler():
            s = baglam.saat_indeksi(an)
            anahtar = (atama.personel_id, s, atama.nokta_id) if s is not None else None
            if anahtar is not None and anahtar in x and anahtar not in sabit_kumesi:
                model.add_hint(x[anahtar], 1)

    ceza_terimleri = []
    ham_terimler: dict[str, cp_model.LinearExprT] = {}
    for kural in kurallar:
        terim = kural.modele_ekle(model, x, baglam)
        if terim is not None:
            ham_terimler[kural.kimlik] = terim
            ceza_terimleri.append(kural.agirlik * terim)
    model.minimize(sum(ceza_terimleri) if ceza_terimleri else 0)

    return model, x, baglam, ham_terimler


def atamalari_bloklara_topla(
    baglam: Baglam, atanan_anahtarlar: frozenset[XAnahtari]
) -> list[AtamaKaydi]:
    """Cozucunun SAAT duzeyindeki ciktisini blok kayitlarina toplar (SDD 4.2.1).

    Cozucu saat duzeyinde sonuc verir; `atama` tablosu blok basina kayit
    tutar. Ardisik calisma saatleri YAZMA ANINDA tek bloga toplanir - saat
    basina satir tutulsaydi her okuma yuzeyi (izgara, manuel duzenleme,
    surum karsilastirmasi, disa aktarma) satirlari yeniden bloklara toplamak
    zorunda kalirdi.

    Birlestirme, kapsama acigi kayitlarininkiyle AYNI YARDIMCIDAN gecer
    (`ardisik_saatleri_grupla`); ikinci bir kopya yazilmaz. Tek fark
    `gun_sinirinda_kes=False`: gece yarisini asan blok TEK KAYITTA durmak
    zorundadir ve `bitis` ertesi gune duser. Etiket gorev noktasidir, cunku
    nokta degistiginde blok kesilmelidir - kesilmemesi halinde tek bir
    kayit iki farkli noktayi tasirdi ve H1'in nokta sabitligi kayitta
    gorunmez olurdu.

    Blogun hangi gune sayildigi (TD-1) baslangictan turetilir.
    """
    saatler: dict[int, list[tuple[int, int]]] = {}
    for p, s, n in atanan_anahtarlar:
        saatler.setdefault(p, []).append((s, n))

    bloklar: list[AtamaKaydi] = []
    for p in sorted(saatler):
        for ilk, son, nokta_id in ardisik_saatleri_grupla(saatler[p], gun_sinirinda_kes=False):
            bloklar.append(
                AtamaKaydi(
                    personel_id=p,
                    baslangic=baglam.saat_zamani(ilk),
                    bitis=baglam.saat_zamani(son) + timedelta(hours=1),
                    nokta_id=nokta_id,
                )
            )
    return bloklar
