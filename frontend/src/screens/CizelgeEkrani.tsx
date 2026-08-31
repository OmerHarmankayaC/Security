import { useCallback, useEffect, useMemo, useState, type PropsWithChildren } from 'react'
import { api, ApiHatasi } from '../api/client'
import type {
  Atama,
  BlokDegisikligi,
  CizelgeSurumu,
  Donem,
  DogrulamaSonucu,
  GorevNoktasi,
  FazlaKadro,
  KapsamaAcigi,
  Kural,
  Personel,
  Yetkinlik,
  Analiz,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { GunIzgarasi } from '../components/GunIzgarasi'
import { HaftaSeridi } from '../components/HaftaSeridi'
import { YazdirmaOnizlemesi } from '../components/YazdirmaOnizlemesi'
import { csvDisaAktar, type CizelgeVerisi } from '../lib/disaAktarma'
import { Buton, Kart, KartEtiketi, Sayi } from '../components/app-ui'
import { cn } from '../lib/utils'
import { belirtmeHaliEki, buyukHarf } from '../lib/metin'
import { sayiBicimle } from '../lib/sayi'
import { blokSinirlariniOku } from '../lib/kuralParametre'
import { sonDonem } from '@/lib/donemSecimi'
import { izgaraSatirlari } from '@/lib/izgaraSatirlari'
import {
  BOS_OTURUM,
  adimlariEkle,
  atamalariUygula,
  bekleyenler,
  blokDegisikligi,
  geriAl,
  geriAlinabilirMi,
  kirliMi,
  tasimaAdimlari,
  yenidenUygula,
  yenidenUygulanabilirMi,
  type Oturum,
} from '../lib/duzenlemeOturumu'
import { sonucuOzetle } from '../lib/sonucDili'
import { saatRengi } from '../lib/saatRengi'
import { BASLANGIC_SAATLERI, BITIS_SAATLERI } from '../lib/talepAraligi'
import { saatEtiketi, sapmaGunu } from '../lib/blok'
import {
  bugunIso,
  donemAraligiBicimle,
  gunBasligiParcalari,
  gunKisaltmasiVeNumarasi,
  gunlerListesi,
  haftaSonuMu,
} from '../lib/tarih'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
  /**
   * "Yeniden Çöz" — Çözüm ekranına geçer ve SEÇİLİ SÜRÜMÜ taban olarak
   * taşır. Sürüm taşınmazsa çözüm dönem için sıfırdan başlar ve sürümün
   * KİLİTLİ atamaları atılır: "elle başla, çözücüye devret" yolu ancak
   * bu bağlantı kurulduğunda çalışır (SDD 5.6).
   */
  yenidenCozIste: (donemId: number, surumId: number | null) => void
}

const BOSALT_DEGERI = ''

/** "Yeniden Çöz" düğmesinin ipucu metni (bkz. düğmenin yanındaki not). */
function yenidenCozIpucu(surum: CizelgeSurumu | null, kilitliSayisi: number): string | undefined {
  if (surum === null) return undefined
  if (kilitliSayisi === 0) {
    return `Sürüm ${surum.surum_no} taban alınarak yeniden çözülür; bu sürümde kilitli atama yok.`
  }
  return `Sürüm ${surum.surum_no} taban alınarak yeniden çözülür; ${kilitliSayisi} kilitli atama korunur.`
}

const SURUM_DURUM_METNI: Record<string, string> = {
  taslak: 'Taslak',
  cozuldu: 'Çözüldü',
  yayinlandi: 'Yayınlandı',
  arsiv: 'Arşiv',
}

const SECIM_SINIFI =
  'h-8 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30 disabled:opacity-50'

interface SeciliHucre {
  personelId: number
  tarih: string
}

/**
 * Ekranın iki görünümü (SDD 6.3.3).
 *
 * GÖREV NOKTASI EKSENİ KALKTI. Önceki sürümde ızgara personel ekseninden
 * nokta eksenine çevrilebiliyordu; o anahtar, satır ekseninin nokta × vardiya
 * TİPİ olduğu kataloglu sürümden kalmaydı ve Tur 5'te zaten yarısını
 * kaybetmişti. SDD 6.3.3 (sürüm 1.28) ekranın iki görünümünü çözünürlük
 * üzerinden tanımlıyor: gün ızgarası ve hafta şeridi. "Bu noktada bugün kim
 * var" sorusu, gün ızgarasının nokta süzgeciyle yanıtlanır.
 */
type Gorunum = 'gun' | 'hafta'

export function CizelgeEkrani({ ekranSec, donemId, donemIdSec, yenidenCozIste }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [excelIniyor, setExcelIniyor] = useState(false)
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [surumId, setSurumId] = useState<number | null>(null)

  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [noktalar, setNoktalar] = useState<GorevNoktasi[]>([])
  // Sürükleme sınırları kural kataloğundan okunur, koda gömülmez (İş 4).
  const [kurallar, setKurallar] = useState<Kural[]>([])

  const [atamalar, setAtamalar] = useState<Atama[]>([])
  const [kapsamaAcigi, setKapsamaAcigi] = useState<KapsamaAcigi[]>([])
  const [fazlaKadro, setFazlaKadro] = useState<FazlaKadro[]>([])
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const [yetkinlikler, setYetkinlikler] = useState<Yetkinlik[]>([])
  const [analiz, setAnaliz] = useState<Analiz | null>(null)
  // Süzgeçler. Üçü de YALNIZCA görünümü daraltır; hiçbir atamayı değiştirmez
  // ve sunucuya gitmez — veri zaten sürümle birlikte tamamı yüklü.
  const [seciliYetkinlikId, setSeciliYetkinlikId] = useState<number | null>(null)
  const [seciliSuzgecNoktaId, setSeciliSuzgecNoktaId] = useState<number | null>(null)
  const [yalnizcaAcik, setYalnizcaAcik] = useState(false)

  const [gorunum, setGorunum] = useState<Gorunum>('gun')
  const [seciliGun, setSeciliGun] = useState<string | null>(null)
  const [yazdirmaAcik, setYazdirmaAcik] = useState(false)
  const [seciliHucre, setSeciliHucre] = useState<SeciliHucre | null>(null)
  // Blok BAŞLANGIÇ ve BİTİŞ SAATİYLE tanımlanır (SDD 6.3.3).
  const [seciliBaslangic, setSeciliBaslangic] = useState<number | null>(null)
  const [seciliBitis, setSeciliBitis] = useState<number | null>(null)
  const [seciliNoktaId, setSeciliNoktaId] = useState<string>(BOSALT_DEGERI)
  const [dogrulamaSonucu, setDogrulamaSonucu] = useState<DogrulamaSonucu | null>(null)
  // TASLAK DÜZENLEME OTURUMU (SRS TD-16). Değişiklikler burada birikir;
  // sunucuya yazma yalnızca Kaydet ile olur.
  const [oturum, setOturum] = useState<Oturum>(BOS_OTURUM)
  const [damga, setDamga] = useState<string | null>(null)
  const [kaydediliyor, setKaydediliyor] = useState(false)
  const [panelYukleniyor, setPanelYukleniyor] = useState(false)
  const [panelHata, setPanelHata] = useState<string | null>(null)

  // Tanim listeleri + donemler: bir kez yuklenir.
  useEffect(() => {
    Promise.all([
      api.donemler(),
      api.personelListele(),
      api.noktaListele(),
      api.yetkinlikListele(),
      api.kuralListele(),
    ])
      .then(([d, p, n, y, k]) => {
        setDonemler(d)
        setPersonelListesi(p)
        setNoktalar(n)
        setYetkinlikler(y.filter((x) => x.aktif))
        setKurallar(k)
        // `d[0]` EN ESKİ dönemdir (uç nokta artan tarihe sıralı döner);
        // varsayılan EN SON dönem olmalı (bkz. lib/donemSecimi.ts).
        if (donemId === null) {
          const son = sonDonem(d)
          if (son) donemIdSec(son.donem_id)
        }
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tanımlar yüklenemedi'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Donem degisince surumleri yukle, en son surumu sec.
  useEffect(() => {
    if (donemId === null) {
      setSurumler([])
      setSurumId(null)
      return
    }
    api
      .surumler(donemId)
      .then((s) => {
        setSurumler(s)
        setSurumId(s[0] ? s[0].surum_id : null)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Sürümler yüklenemedi'))
  }, [donemId])

  // Üst şeritteki KAPSAMA ve TOPLAM CEZA sayıları analizden gelir. Izgara
  // verisinden AYRI çekilir: ikisi farklı hızda değişir (elle yapılan bir
  // atama düzenlemesi ızgarayı hemen tazeler, analiz sürüme bağlıdır) ve
  // analizin gecikmesi ızgaranın açılmasını bekletmemelidir.
  useEffect(() => {
    if (surumId === null) {
      setAnaliz(null)
      return
    }
    api
      .analizGetir(surumId)
      .then(setAnaliz)
      // Şerit salt bilgilendirme: analiz gelmezse "—" yazar, ızgara çalışır.
      .catch(() => setAnaliz(null))
  }, [surumId])

  const surumYukle = () => {
    if (surumId === null) {
      setAtamalar([])
      setKapsamaAcigi([])
      setFazlaKadro([])
      return
    }
    setYukleniyor(true)
    setHata(null)
    Promise.all([
      api.surumAtamalari(surumId),
      api.surumKapsamaAcigi(surumId),
      api.surumFazlaKadro(surumId),
    ])
      .then(([a, k, f]) => {
        setAtamalar(a)
        setKapsamaAcigi(k)
        setFazlaKadro(f)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Çizelge yüklenemedi'))
      .finally(() => setYukleniyor(false))
  }

  useEffect(surumYukle, [surumId])

  /**
   * Sürüm değişince oturum SIFIRLANIR ve yeni damga alınır.
   *
   * Damga, kullanıcının düzenlemeye başladığı andaki sürüm hâlini gösterir;
   * kaydederken geri gönderilir. Başka bir oturum arada kaydetmişse damga
   * değişmiş olur ve kayıt reddedilir (SDD 5.5.1).
   */
  useEffect(() => {
    setOturum(BOS_OTURUM)
    setDogrulamaSonucu(null)
    setSeciliHucre(null)
    setDamga(surumler.find((s) => s.surum_id === surumId)?.damga ?? null)
  }, [surumId, surumler])

  const donem = donemler.find((d) => d.donem_id === donemId) ?? null
  const surum = surumler.find((s) => s.surum_id === surumId) ?? null

  // Yalnizca taslak ve cozuldu duzenlenebilir; yayinlanmis/arsiv surumde
  // sunucu 409 doner (services/dogrulama_servisi.py).
  const surumDuzenlenebilir =
    surum !== null && (surum.durum === 'taslak' || surum.durum === 'cozuldu')

  // "Yeniden Çöz" ipucu bunu yazar. KAYDEDİLMİŞ atamalardan sayılır —
  // düğme zaten kirli oturumda pasif, yani ekrandaki kilit ile sunucudaki
  // kilit bu noktada aynıdır.
  const kilitliAtamaSayisi = useMemo(() => atamalar.filter((a) => a.kilitli).length, [atamalar])

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )
  const noktaMap = useMemo(() => new Map(noktalar.map((n) => [n.nokta_id, n])), [noktalar])
  const sinirlar = useMemo(() => blokSinirlariniOku(kurallar), [kurallar])

  const donemGunleri = useMemo(
    () => (donem ? gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi) : []),
    [donem],
  )
  // Bugun isareti icin: bileşen saat OKUMAZ demek burada gecerli degil —
  // isaret tanimi geregi "su anki gun"e bagli. lib/tarih.ts'ten gecer.
  const bugun = bugunIso()

  const seritNoktalari = useMemo(
    () => noktalar.filter((n) => n.aktif).sort((a, b) => a.nokta_id - b.nokta_id),
    [noktalar],
  )

  // Tarih → o gün açık veren nokta kimlikleri.
  const acikNoktalar = useMemo(() => {
    const indeks = new Map<string, Map<number, number>>()
    for (const k of kapsamaAcigi) {
      // Açık başladığı güne sayılır (B-23 sonrası: gün, başlangıç
      // damgasından türetilir).
      const tarih = sapmaGunu(k)
      let gun = indeks.get(tarih)
      if (!gun) {
        gun = new Map()
        indeks.set(tarih, gun)
      }
      gun.set(k.nokta_id, (gun.get(k.nokta_id) ?? 0) + k.eksik_sayi)
    }
    return indeks
  }, [kapsamaAcigi])

  const gunler = useMemo(
    () => (yalnizcaAcik ? donemGunleri.filter((g) => acikNoktalar.has(g)) : donemGunleri),
    [donemGunleri, yalnizcaAcik, acikNoktalar],
  )

  // Seçili gün her zaman gösterilen günlerden biri olmalı: dönem değiştiğinde
  // ya da süzgeç günü listeden düşürdüğünde ekran boş bir güne bakamaz.
  useEffect(() => {
    if (gunler.length === 0) {
      setSeciliGun(null)
      return
    }
    setSeciliGun((mevcut) =>
      mevcut && gunler.includes(mevcut) ? mevcut : (gunler.find((g) => g === bugun) ?? gunler[0]!),
    )
  }, [gunler, bugun])

  /**
   * Izgaranın GÖRDÜĞÜ atamalar: sürümün atamaları + biriken değişiklikler.
   *
   * Değişiklik bırakıldığı anda burada görünür; sunucu yanıtı beklenmez
   * (SRS TD-16). Kaydedilmemiş bloklar negatif kimlik taşır.
   */
  const gosterilenAtamalar = useMemo(
    () => atamalariUygula(atamalar, bekleyenler(oturum)),
    [atamalar, oturum],
  )

  // Süzgeçten ÖNCEKİ liste — alttaki "36 personelin 10'u gösteriliyor"
  // satırının paydası budur; süzgeç değiştikçe payda oynamamalı.
  //
  // Düzenlenebilir sürümde satırlar KADRODAN gelir (bkz. lib/izgaraSatirlari.ts)
  // — boş bir taslakta tıklanacak hücre kalması için ataması olmayan personel
  // de satır olmalıdır. Salt okunurda satırlar ATAMALARDAN gelir; orada soru
  // "ne karar verildi"dir ve boş satır gürültüdür.
  const tumIzgaraPersonelleri = useMemo(
    () =>
      izgaraSatirlari({
        personeller: personelListesi,
        atamalar: gosterilenAtamalar,
        duzenlenebilir: surumDuzenlenebilir,
        donemBaslangic: donem?.baslangic_tarihi ?? '',
        donemBitis: donem?.bitis_tarihi ?? '',
      }),
    [personelListesi, gosterilenAtamalar, surumDuzenlenebilir, donem],
  )

  // Nokta süzgeci personeli DÖNEM BOYUNCA o noktada çalışanlarla sınırlar.
  // Gün bazında daraltmak, günler arasında gezinirken satırların altından
  // kayıp gitmesine yol açardı.
  const noktaPersonelleri = useMemo(() => {
    if (seciliSuzgecNoktaId === null) return null
    return new Set(
      gosterilenAtamalar
        .filter((a) => a.nokta_id === seciliSuzgecNoktaId)
        .map((a) => a.personel_id),
    )
  }, [gosterilenAtamalar, seciliSuzgecNoktaId])

  const izgaraPersonelleri = useMemo(
    () =>
      tumIzgaraPersonelleri
        .filter(
          (p) =>
            seciliYetkinlikId === null || p.yetkinlik_idleri.includes(seciliYetkinlikId),
        )
        .filter((p) => noktaPersonelleri === null || noktaPersonelleri.has(p.personel_id)),
    [tumIzgaraPersonelleri, seciliYetkinlikId, noktaPersonelleri],
  )

  // Izgaraya giden atamalar: nokta süzgeci seçiliyse yalnızca o noktanınkiler
  // çizilir — aksi hâlde süzgeç satırları daraltır ama şeritler aynı kalır ve
  // süzgeç hiçbir şey yapmamış gibi görünür.
  const izgaraAtamalari = useMemo(
    () =>
      seciliSuzgecNoktaId === null
        ? gosterilenAtamalar
        : gosterilenAtamalar.filter((a) => a.nokta_id === seciliSuzgecNoktaId),
    [gosterilenAtamalar, seciliSuzgecNoktaId],
  )

  const atamaIndeksi = useMemo(() => {
    const indeks = new Map<string, Atama>()
    for (const a of gosterilenAtamalar) indeks.set(`${a.personel_id}|${a.tarih}`, a)
    return indeks
  }, [gosterilenAtamalar])

  const atamaBul = (personelId: number, tarih: string): Atama | undefined =>
    atamaIndeksi.get(`${personelId}|${tarih}`)

  const hucreSec = (personelId: number, tarih: string) => {
    setSeciliHucre({ personelId, tarih })
    const mevcut = atamaBul(personelId, tarih)
    setSeciliBaslangic(mevcut ? Number(mevcut.baslangic_zamani.slice(11, 13)) : null)
    setSeciliBitis(mevcut ? bitisSaatiOku(mevcut) : null)
    setSeciliNoktaId(mevcut ? String(mevcut.nokta_id) : BOSALT_DEGERI)
    setPanelHata(null)
  }

  /**
   * Oturuma adım ekler ve SUNUCUYA DOĞRULATIR (SRS TD-16).
   *
   * Değişiklik ızgarada anında görünür — sunucunun yanıtı beklenmez. Yanıt
   * geldiğinde yalnızca SONUÇ ŞERİDİ tazelenir; değişikliğin kendisi zaten
   * uygulanmıştır ve kaydedilene kadar yalnızca istemcide durur.
   *
   * İstek son adımı değil BİRİKİMİN TAMAMINI taşır: tek tek geçerli olan iki
   * değişiklik birlikte bir kuralı bozabilir (SDD 5.5).
   */
  const adimlariIsle = useCallback(
    (adimlar: BlokDegisikligi[]) => {
      if (surumId === null) return
      setOturum((mevcut) => {
        const yeni = adimlariEkle(mevcut, adimlar)
        void dogrulamayiTazele(surumId, bekleyenler(yeni))
        return yeni
      })
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [surumId],
  )

  const dogrulamayiTazele = async (id: number, bekleyen: BlokDegisikligi[]) => {
    setPanelYukleniyor(true)
    setPanelHata(null)
    try {
      setDogrulamaSonucu(await api.atamaDogrula({ surum_id: id, degisiklikler: bekleyen }))
    } catch (e) {
      setPanelHata(e instanceof Error ? e.message : 'Doğrulama başarısız')
    } finally {
      setPanelYukleniyor(false)
    }
  }

  // --- Izgaranın beş eylemi (İş 1) -----------------------------------------

  const blokTanimla = (personelId: number, baslangic: number, bitis: number) => {
    if (!seciliGun) return
    // Görev noktası: o günün mevcut bloğundan devralınır (SRS H1 — nokta blok
    // boyunca tektir). Blok yoksa ilk nokta seçilir; kullanıcı menüden
    // değiştirebilir. Noktasız bir blok sunucuya gönderilemez.
    const mevcut = atamaBul(personelId, seciliGun)
    const noktaId = mevcut?.nokta_id ?? seritNoktalari[0]?.nokta_id
    if (noktaId === undefined) return
    hucreSec(personelId, seciliGun)
    adimlariIsle([blokDegisikligi(personelId, seciliGun, { baslangic, bitis, noktaId })])
  }

  const blokTasi = (
    kaynakId: number,
    hedefId: number,
    baslangic: number,
    bitis: number,
  ) => {
    if (!seciliGun) return
    const kaynak = atamaBul(kaynakId, seciliGun)
    if (!kaynak) return
    const aralik = { baslangic, bitis, noktaId: kaynak.nokta_id }
    hucreSec(hedefId, seciliGun)
    // Aynı satırda kaydırma da "taşıma"dır; kaynakla hedef aynı olduğunda
    // kaldırma adımı gereksizdir ve atlanır.
    adimlariIsle(
      kaynakId === hedefId
        ? [blokDegisikligi(hedefId, seciliGun, aralik)]
        : tasimaAdimlari(kaynakId, hedefId, seciliGun, aralik),
    )
  }

  const noktaDegistir = (personelId: number, noktaId: number) => {
    if (!seciliGun) return
    const mevcut = atamaBul(personelId, seciliGun)
    if (!mevcut) return
    adimlariIsle([
      blokDegisikligi(personelId, seciliGun, {
        baslangic: Number(mevcut.baslangic_zamani.slice(11, 13)),
        bitis: bitisSaatiOku(mevcut),
        noktaId,
      }),
    ])
  }

  const blokSil = (personelId: number) => {
    if (!seciliGun) return
    adimlariIsle([blokDegisikligi(personelId, seciliGun, null)])
  }

  /**
   * Kilit oturumun DIŞINDADIR ve anında yazılır.
   *
   * Kilit atamanın kendisini değiştirmez; yalnızca yeniden çözümde sabit
   * girdi sayılıp sayılmayacağını belirler (FR-6.5) ve hiçbir kuralı
   * etkilemez. Oturuma alınsaydı, kaydedilmemiş bir kilit "bu blok korunuyor"
   * diye görünür ama yeniden çözüm onu görmezdi.
   */
  const kilidiDegistir = async (personelId: number, kilitli: boolean) => {
    if (surumId === null || !seciliGun) return
    setPanelHata(null)
    try {
      await api.atamaKilitAyarla(surumId, personelId, seciliGun, kilitli)
      surumYukle()
    } catch (e) {
      setPanelHata(e instanceof Error ? e.message : 'Kilit değiştirilemedi')
    }
  }

  // --- Oturum eylemleri (İş 2b) --------------------------------------------

  const geriAlEylemi = () => {
    if (surumId === null) return
    setOturum((mevcut) => {
      const yeni = geriAl(mevcut)
      void dogrulamayiTazele(surumId, bekleyenler(yeni))
      return yeni
    })
  }

  const yenidenUygulaEylemi = () => {
    if (surumId === null) return
    setOturum((mevcut) => {
      const yeni = yenidenUygula(mevcut)
      void dogrulamayiTazele(surumId, bekleyenler(yeni))
      return yeni
    })
  }

  const oturumuAt = () => {
    setOturum(BOS_OTURUM)
    setDogrulamaSonucu(null)
    setPanelHata(null)
  }

  /**
   * Kaydedilmemiş değişiklikle sekmeyi kapatmaya çalışan kullanıcı uyarılır
   * (FR-6.8).
   *
   * Tarayıcı kendi metnini gösterir; `preventDefault` uyarıyı tetiklemenin
   * standart yoludur. Ekran İÇİ geçişler (dönem/sürüm değiştirme, yeniden
   * çözme) ayrıca korunuyor: ilgili denetimler oturum kirliyken kapalı.
   */
  useEffect(() => {
    if (!kirliMi(oturum)) return
    const uyar = (e: BeforeUnloadEvent) => e.preventDefault()
    window.addEventListener('beforeunload', uyar)
    return () => window.removeEventListener('beforeunload', uyar)
  }, [oturum])

  const kaydet = async () => {
    if (surumId === null || damga === null) return
    setKaydediliyor(true)
    setPanelHata(null)
    try {
      const sonuc = await api.atamaKaydet({
        surum_id: surumId,
        damga,
        degisiklikler: bekleyenler(oturum),
      })
      // Sunucu YENİ damgayı döndürür; bir sonraki kayıt onunla korunur.
      if (sonuc.damga) setDamga(sonuc.damga)
      setOturum(BOS_OTURUM)
      setDogrulamaSonucu(null)
      surumYukle()
    } catch (e) {
      if (e instanceof ApiHatasi && e.status === 409) {
        // 409'un üç nedeni var ve üçü de kullanıcıya başka şey söyler.
        setPanelHata(
          typeof e.detay === 'string'
            ? e.detay
            : 'Kaydedilemedi: değişiklikler zorunlu bir kuralı bozuyor.',
        )
      } else {
        setPanelHata(e instanceof Error ? e.message : 'Kaydedilemedi')
      }
    } finally {
      setKaydediliyor(false)
    }
  }

  /**
   * "Boş Taslak Aç" (FR-7.3) — atamasız bir taslak sürüm üretir. Taslak bu
   * ekranda ELLE doldurulabilir ya da olduğu gibi çözücüye bırakılabilir;
   * varlık nedeni artık bu iki yolun ikisi de.
   *
   * Dönemde zaten sürüm varsa kullanıcı sayıyla uyarılır: yanlışlıkla
   * dolu bir sürümün yanına boş bir tane daha açmak kolay geri alınmaz.
   * Sürüm hiç yoksa uyarı gereksizdir, doğrudan açılır.
   */
  const bosTaslakAc = () => {
    if (donemId === null) return
    if (
      surumler.length > 0 &&
      !window.confirm(
        `Dönemde ${surumler.length} sürüm var; ${surumler.length + 1}. sürüm boş bir taslak olarak açılacak.`,
      )
    ) {
      return
    }
    api
      .bosTaslakAc(donemId)
      .then((yeni) =>
        api.surumler(donemId).then((s) => {
          setSurumler(s)
          setSurumId(yeni.surum_id)
        }),
      )
      .catch((e) => setHata(e instanceof Error ? e.message : 'Boş taslak açılamadı'))
  }

  // Dışa aktarma verisi Çizelge ve Analiz ekranlarında aynı biçimde kurulur;
  // biçimleme ve indirme lib/disaAktarma.ts'te ortaktır.
  const disaAktarmaVerisi: CizelgeVerisi | null =
    donem && surum
      ? {
          donem,
          surum,
          atamalar,
          kapsamaAcigi,
          fazlaKadro,
          personelMap,
          noktaMap,
        }
      : null

  const seciliPersonel = seciliHucre ? personelMap.get(seciliHucre.personelId) : null

  return (
    <AppShell
      aktifEkran="Çizelge"
      ekranSec={ekranSec}
      baslik="Çizelge"
      altBaslik={
        surum ? (
          <span className="mono-caps rounded-sm bg-sunken px-2 py-1 text-ink-muted">
            {buyukHarf(SURUM_DURUM_METNI[surum.durum] ?? surum.durum)} · SÜRÜM {surum.surum_no}
          </span>
        ) : undefined
      }
      aksiyonlar={
        <>
          {/* İki görünüm (SDD 6.3.3): aynı veriyi iki farklı ÇÖZÜNÜRLÜKTE
              gösterirler. Gün ızgarası ana görünümdür; hafta şeridi genel
              dağılımı verir ve bir güne tıklayınca ızgaraya geçer. */}
          <div className="flex rounded-sm bg-chrome-raised p-0.5">
            {(
              [
                ['gun', 'Gün'],
                ['hafta', 'Hafta'],
              ] as const
            ).map(([secenek, etiket]) => (
              <button
                key={secenek}
                type="button"
                aria-pressed={gorunum === secenek}
                onClick={() => setGorunum(secenek)}
                className={cn(
                  'rounded-sm px-3 py-1.5 text-sm transition-colors',
                  gorunum === secenek
                    ? 'bg-accent font-medium text-chrome-ink'
                    : 'text-chrome-ink-muted hover:text-chrome-ink',
                )}
              >
                {etiket}
              </button>
            ))}
          </div>
          {/* EXCEL SUNUCUDAN, CSV TARAYICIDAN. Çalışma kitabı biçimlemeyi
              (saat bandı dolgusu, formüller, grafik) taşır; onu istemcide
              kurmak biçimin ikinci bir tanımı olurdu. CSV ham veridir ve
              zaten elde duran veriden üretilir. */}
          <Buton
            varyant="ikincil"
            disabled={surum === null || excelIniyor}
            title="Çizelge + özet + ham veri, biçimlenmiş çalışma kitabı"
            onClick={() => {
              if (!surum) return
              setExcelIniyor(true)
              api
                .cizelgeExcelIndir(surum.surum_id, surum.surum_no)
                .catch(() => setHata('Excel dosyası indirilemedi.'))
                .finally(() => setExcelIniyor(false))
            }}
          >
            {excelIniyor ? 'İndiriliyor…' : 'Excel'}
          </Buton>
          <Buton
            varyant="ikincil"
            disabled={disaAktarmaVerisi === null}
            title="Uzun biçim CSV + talep sapması dosyası (ham veri)"
            onClick={() => disaAktarmaVerisi && csvDisaAktar(disaAktarmaVerisi)}
          >
            CSV
          </Buton>
          <Buton
            varyant="ikincil"
            disabled={disaAktarmaVerisi === null}
            title="Personel × saat ızgarası, yatay A4"
            onClick={() => setYazdirmaAcik(true)}
          >
            Yazdır
          </Buton>
          {/* OTURUM ÇUBUĞU (SRS FR-6.7, FR-6.8). Kaydedilmemiş değişiklik
              varken sayısı görünür; Kaydet tek istek gönderir. */}
          {surumDuzenlenebilir && kirliMi(oturum) && (
            <>
              <span className="mono-caps rounded-sm bg-signal-soft px-2 py-1 text-signal">
                {bekleyenler(oturum).length} KAYDEDİLMEMİŞ
              </span>
              <Buton
                varyant="ikincil"
                disabled={!geriAlinabilirMi(oturum) || kaydediliyor}
                title="Son değişikliği geri al"
                onClick={geriAlEylemi}
              >
                Geri Al
              </Buton>
              <Buton
                varyant="ikincil"
                disabled={!yenidenUygulanabilirMi(oturum) || kaydediliyor}
                title="Geri alınan değişikliği yeniden uygula"
                onClick={yenidenUygulaEylemi}
              >
                Yinele
              </Buton>
              <Buton varyant="hayalet" disabled={kaydediliyor} onClick={oturumuAt}>
                Vazgeç
              </Buton>
              <Buton varyant="birincil" disabled={kaydediliyor} onClick={kaydet}>
                {kaydediliyor ? 'Kaydediliyor…' : 'Kaydet'}
              </Buton>
            </>
          )}
          <Buton
            varyant="birincil"
            disabled={donemId === null || kirliMi(oturum)}
            // DÜĞMENİN NE YAPACAĞI YAZILI OLMALI: seçili sürüm taban alınır
            // ve kilitli atamalar korunur, kalanını çözücü yeniden yazar.
            // Kilit sayısı da yazılır — "kilitliler korunur" cümlesi, hiç
            // kilit yokken kullanıcıya yanlış bir güvence verirdi.
            title={
              kirliMi(oturum)
                ? 'Önce değişiklikleri kaydedin ya da vazgeçin'
                : yenidenCozIpucu(surum, kilitliAtamaSayisi)
            }
            onClick={() => donemId !== null && yenidenCozIste(donemId, surumId)}
          >
            Yeniden Çöz
          </Buton>
        </>
      }
    >
      {yazdirmaAcik && disaAktarmaVerisi && (
        <YazdirmaOnizlemesi veri={disaAktarmaVerisi} onKapat={() => setYazdirmaAcik(false)} />
      )}

      <Kart>
        <KartEtiketi>seçim</KartEtiketi>
        <div className="flex flex-wrap items-end gap-6">
          <div className="flex flex-col gap-1">
            <label htmlFor="donem-sec" className="text-sm text-ink-muted">
              Dönem
            </label>
            <select
              id="donem-sec"
              className={SECIM_SINIFI}
              // Kirli oturumda dönem/sürüm değiştirmek birikimi sessizce
              // atardı; kullanıcı önce kaydeder ya da vazgeçer (FR-6.8).
              disabled={kirliMi(oturum)}
              title={kirliMi(oturum) ? 'Önce değişiklikleri kaydedin ya da vazgeçin' : undefined}
              value={donemId ?? ''}
              onChange={(e) => donemIdSec(e.target.value ? Number(e.target.value) : null)}
            >
              {donemler.map((d) => (
                <option key={d.donem_id} value={d.donem_id}>
                  {donemAraligiBicimle(d.baslangic_tarihi, d.bitis_tarihi)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="surum-sec" className="text-sm text-ink-muted">
              Sürüm
            </label>
            <select
              id="surum-sec"
              className={SECIM_SINIFI}
              disabled={kirliMi(oturum)}
              title={kirliMi(oturum) ? 'Önce değişiklikleri kaydedin ya da vazgeçin' : undefined}
              value={surumId ?? ''}
              onChange={(e) => setSurumId(e.target.value ? Number(e.target.value) : null)}
            >
              {surumler.map((s) => (
                <option key={s.surum_id} value={s.surum_id}>
                  Sürüm {s.surum_no} ({SURUM_DURUM_METNI[s.durum] ?? s.durum})
                </option>
              ))}
            </select>
          </div>
          <Buton
            varyant="ikincil"
            disabled={donemId === null || kirliMi(oturum)}
            title={kirliMi(oturum) ? 'Önce değişiklikleri kaydedin ya da vazgeçin' : undefined}
            onClick={bosTaslakAc}
          >
            Boş Taslak Aç
          </Buton>
        </div>
      </Kart>

      {hata && <p className="text-sm text-signal">{hata}</p>}

      {/* YAYINLANMIŞ SÜRÜM SALT OKUNURDUR (SRS FR-6.9). Araçların gizlenmesi
          tek başına yeterli değil — sunucu isteği ayrıca reddeder (SDD
          5.5.2) — ama kullanıcının NEDEN düzenleyemediğini burada okuması
          gerekir, yoksa ızgaranın tepkisizliği hataya benzer. */}
      {surum !== null && !surumDuzenlenebilir && (
        <p className="m-0 rounded-sm border-l-2 border-accent bg-accent-soft px-4 py-3 text-sm text-ink">
          <strong className="font-medium">
            {SURUM_DURUM_METNI[surum.durum] ?? surum.durum} durumundaki sürüm salt okunur.
          </strong>{' '}
          Değişiklik için Sürümler ekranında bu sürümün{' '}
          <strong className="font-medium">“Düzenlemek İçin Kopyala”</strong> düğmesini kullanın —
          çizelge olduğu gibi yeni taslağa taşınır. “Boş Taslak Aç” ise atamasız bir sürüm üretir;
          onu bu ekranda elle doldurabilir ya da çözücüye bırakabilirsiniz (FR-7.3).
        </p>
      )}

      {/* Süzgeç ve ölçüm şeridi. Solda ızgarayı daraltan süzgeçler, sağda
          sürümün üç ölçüsü. */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-rule pb-4">
        <span className="etiket-caps text-ink-muted">{buyukHarf('Süzgeç')}</span>
        <div className="flex flex-wrap items-center gap-2">
          <SuzgecCipi secili={seciliYetkinlikId === null} onSec={() => setSeciliYetkinlikId(null)}>
            Tüm yetkinlikler
          </SuzgecCipi>
          {yetkinlikler.map((y) => (
            <SuzgecCipi
              key={y.yetkinlik_id}
              secili={seciliYetkinlikId === y.yetkinlik_id}
              onSec={() => setSeciliYetkinlikId(y.yetkinlik_id)}
            >
              {y.ad}
            </SuzgecCipi>
          ))}
          {/* Nokta süzgeci, kalkan nokta EKSENİNİN yerini tutar: "bu noktada
              bugün kim var" sorusu gün ızgarasında bu süzgeçle yanıtlanır. */}
          <span className="mx-1 h-5 w-px bg-rule" />
          <SuzgecCipi
            secili={seciliSuzgecNoktaId === null}
            onSec={() => setSeciliSuzgecNoktaId(null)}
          >
            Tüm noktalar
          </SuzgecCipi>
          {seritNoktalari.map((n) => (
            <SuzgecCipi
              key={n.nokta_id}
              secili={seciliSuzgecNoktaId === n.nokta_id}
              onSec={() => setSeciliSuzgecNoktaId(n.nokta_id)}
            >
              {n.ad}
            </SuzgecCipi>
          ))}
          <SuzgecCipi secili={yalnizcaAcik} onSec={() => setYalnizcaAcik(!yalnizcaAcik)}>
            Yalnızca açık verilen günler
          </SuzgecCipi>
        </div>

        <div className="ml-auto flex items-center gap-4">
          <Olcum etiket="Kapsama">
            {analiz ? `%${Math.round(analiz.kapsama_orani * 100)}` : '—'}
          </Olcum>
          <span className="h-5 w-px bg-rule" />
          <Olcum etiket="Açık" vurgulu={kapsamaAcigi.length > 0}>
            {sayiBicimle(kapsamaAcigi.length)}
          </Olcum>
          <span className="h-5 w-px bg-rule" />
          <Olcum etiket="Toplam Ceza">
            {analiz?.toplam_ceza != null ? sayiBicimle(Math.round(analiz.toplam_ceza)) : '—'}
          </Olcum>
        </div>
      </div>

      <Kart>
        {yukleniyor ? (
          <p className="text-sm text-ink-muted">Yükleniyor…</p>
        ) : tumIzgaraPersonelleri.length === 0 && !surumDuzenlenebilir ? (
          <p className="text-sm text-ink-muted">Bu sürümde henüz atama yok.</p>
        ) : tumIzgaraPersonelleri.length === 0 ? (
          // Düzenlenebilir sürümde satırlar kadrodan gelir (lib/izgaraSatirlari.ts);
          // burada boş kalmak "atama yok" değil "kadroda kimse yok" demektir.
          <p className="text-sm text-ink-muted">
            Bu dönemde aktif personel yok; Tanımlar ekranından personel ekleyin.
          </p>
        ) : gunler.length === 0 ? (
          <p className="text-sm text-ink-muted">
            Bu dönemde açık verilen gün yok. Süzgeci kaldırarak tüm günleri görebilirsiniz.
          </p>
        ) : izgaraPersonelleri.length === 0 ? (
          <p className="text-sm text-ink-muted">
            Seçili süzgeçlerde bu sürüme atanmış personel yok.
          </p>
        ) : gorunum === 'gun' ? (
          <>
            {/* Gün sekmeleri (SDD 6.3.3). Yirmi sekiz günlük bir dönemde
                yatay kayar; seçili gün her zaman görünür kalır. */}
            <div
              className="mb-3 flex gap-1 overflow-x-auto border-b border-rule pb-2"
              role="tablist"
              aria-label="Gün seçimi"
            >
              {gunler.map((g) => {
                const { kisaltma, numara } = gunBasligiParcalari(g)
                const acik = acikNoktalar.get(g)
                return (
                  <button
                    key={g}
                    type="button"
                    role="tab"
                    aria-selected={seciliGun === g}
                    onClick={() => setSeciliGun(g)}
                    className={cn(
                      'flex shrink-0 flex-col items-center rounded-sm border px-2.5 py-1 font-mono text-mono-kucuk transition-colors',
                      seciliGun === g
                        ? 'border-accent bg-accent-soft font-semibold text-accent'
                        : 'border-transparent text-ink-muted hover:text-ink',
                      haftaSonuMu(g) && seciliGun !== g && 'bg-sunken',
                    )}
                  >
                    <span>{kisaltma}</span>
                    <span className={cn(g === bugun && 'underline underline-offset-2')}>
                      {numara}
                    </span>
                    {acik && (
                      <span className="text-[9px] leading-none font-semibold text-signal">
                        ▲{[...acik.values()].reduce((t, s) => t + s, 0)}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            {seciliGun && (
              <GunIzgarasi
                gun={seciliGun}
                personeller={izgaraPersonelleri}
                atamalar={izgaraAtamalari}
                noktaMap={noktaMap}
                kapsamaAcigi={
                  seciliSuzgecNoktaId === null
                    ? kapsamaAcigi
                    : kapsamaAcigi.filter((k) => k.nokta_id === seciliSuzgecNoktaId)
                }
                seritNoktalari={
                  seciliSuzgecNoktaId === null
                    ? seritNoktalari
                    : seritNoktalari.filter((n) => n.nokta_id === seciliSuzgecNoktaId)
                }
                sinirlar={sinirlar}
                duzenlenebilir={surumDuzenlenebilir}
                seciliPersonelId={seciliHucre?.personelId ?? null}
                onSatirSec={(personelId) => hucreSec(personelId, seciliGun)}
                onBlokTanimla={blokTanimla}
                onBlokTasi={blokTasi}
                onNoktaDegistir={noktaDegistir}
                onKilitDegistir={kilidiDegistir}
                onBlokSil={blokSil}
              />
            )}
          </>
        ) : (
          <HaftaSeridi
            gunler={gunler}
            personeller={izgaraPersonelleri}
            atamalar={izgaraAtamalari}
            noktaMap={noktaMap}
            kapsamaAcigi={
              seciliSuzgecNoktaId === null
                ? kapsamaAcigi
                : kapsamaAcigi.filter((k) => k.nokta_id === seciliSuzgecNoktaId)
            }
            bugun={bugun}
            onGunSec={(g) => {
              setSeciliGun(g)
              setGorunum('gun')
            }}
          />
        )}

        {/* Izgara altı: solda ne kadarının gösterildiği, sağda RENK BANDI.
            Band sürekli olduğu için üç kutulu bir lejant yanlış olurdu —
            gösterilen şey bandın kendisi ve iki ucunun saatidir. */}
        {!yukleniyor && izgaraPersonelleri.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink-muted">
            <span>
              <Sayi>{sayiBicimle(tumIzgaraPersonelleri.length)}</Sayi> personelin{' '}
              <Sayi>{sayiBicimle(izgaraPersonelleri.length)}</Sayi>
              {belirtmeHaliEki(izgaraPersonelleri.length)} gösteriliyor
              {gorunum === 'gun' && seciliGun && ` · ${gunKisaltmasiVeNumarasi(seciliGun)}`}
            </span>
            <div className="ml-auto flex flex-wrap items-center gap-4">
              <SaatBandiLejandi />
              <Lejant sinif="border-2 border-accent bg-surface">Kilitli</Lejant>
              <span className="flex items-center gap-2 text-sm text-ink-muted">
                <span className="font-mono text-xs font-semibold text-signal">▲</span>
                Kapsama açığı
              </span>
            </div>
          </div>
        )}
      </Kart>

      {/* Sonuç şeridi ve ikincil form YAN YANA: ızgaranın altında ayrı bir
          kutu değil. Kullanıcı hangi hücreye ne yaptığını ızgarada görürken
          sonucu da aynı bakışta okumalı. */}
      {(dogrulamaSonucu !== null || panelHata !== null || seciliHucre !== null) && (
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <Kart>
            <KartEtiketi>sonuç</KartEtiketi>
            {panelHata && <p className="m-0 text-sm text-signal">{panelHata}</p>}
            {panelYukleniyor && !dogrulamaSonucu && (
              <p className="m-0 text-sm text-ink-muted">Değerlendiriliyor…</p>
            )}
            {dogrulamaSonucu && <SonucSeridi sonuc={dogrulamaSonucu} personelMap={personelMap} />}
          </Kart>

          {seciliHucre && seciliPersonel && (
            <Kart>
              <KartEtiketi>saat gir</KartEtiketi>
              {/* İKİNCİL YOL (SRS 5.6). Birincil yol ızgaradır; bu form tam
                  değer yazmak isteyen kullanıcı içindir. */}
              <p className="m-0 text-sm text-ink">
                {seciliPersonel.ad_soyad} — {gunKisaltmasiVeNumarasi(seciliHucre.tarih)}
              </p>
              <div className="mt-3 flex flex-col gap-3">
                <div className="flex gap-2">
                  <label className="flex flex-1 flex-col gap-1 text-sm text-ink-muted">
                    Başlangıç
                    <select
                      className={SECIM_SINIFI}
                      value={seciliBaslangic ?? ''}
                      disabled={!surumDuzenlenebilir}
                      onChange={(e) => setSeciliBaslangic(Number(e.target.value))}
                    >
                      <option value="">—</option>
                      {BASLANGIC_SAATLERI.map((x) => (
                        <option key={x} value={x}>
                          {saatEtiketi(x)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="flex flex-1 flex-col gap-1 text-sm text-ink-muted">
                    Bitiş
                    <select
                      className={SECIM_SINIFI}
                      value={seciliBitis ?? ''}
                      disabled={!surumDuzenlenebilir || seciliBaslangic === null}
                      onChange={(e) => setSeciliBitis(Number(e.target.value))}
                    >
                      <option value="">—</option>
                      {BITIS_SAATLERI.map((x) => (
                        <option key={x} value={x}>
                          {saatEtiketi(x)}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label className="flex flex-col gap-1 text-sm text-ink-muted">
                  Görev Noktası
                  <select
                    className={SECIM_SINIFI}
                    value={seciliNoktaId}
                    disabled={!surumDuzenlenebilir}
                    onChange={(e) => setSeciliNoktaId(e.target.value)}
                  >
                    <option value={BOSALT_DEGERI}>—</option>
                    {noktalar.map((n) => (
                      <option key={n.nokta_id} value={n.nokta_id}>
                        {n.ad}
                      </option>
                    ))}
                  </select>
                </label>
                <Buton
                  varyant="ikincil"
                  disabled={
                    !surumDuzenlenebilir ||
                    seciliBaslangic === null ||
                    seciliBitis === null ||
                    seciliNoktaId === BOSALT_DEGERI
                  }
                  onClick={() => {
                    if (seciliBaslangic === null || seciliBitis === null) return
                    adimlariIsle([
                      blokDegisikligi(seciliHucre.personelId, seciliHucre.tarih, {
                        baslangic: seciliBaslangic,
                        bitis: seciliBitis,
                        noktaId: Number(seciliNoktaId),
                      }),
                    ])
                  }}
                >
                  Uygula
                </Buton>
              </div>
            </Kart>
          )}
        </div>
      )}

    </AppShell>
  )
}

/** Bloğun bitiş saati; gün sonu `24` yazılır (00.00 sıfır uzunluk düşündürür). */
function bitisSaatiOku(atama: Atama): number {
  const saat = Number(atama.bitis_zamani.slice(11, 13))
  return saat === 0 ? 24 : saat
}

/**
 * Süzgeç çipi — Tanımlar sekme çubuğuyla aynı dil: aktif `accent-soft`
 * zemin + `accent` metin, pasif zeminsiz + `ink-muted`.
 */
function SuzgecCipi({
  children,
  secili,
  onSec,
}: PropsWithChildren<{ secili: boolean; onSec: () => void }>) {
  return (
    <button
      type="button"
      aria-pressed={secili}
      onClick={onSec}
      className={cn(
        'rounded-sm border px-3 py-1.5 text-sm transition-colors',
        secili
          ? 'border-accent bg-accent-soft font-medium text-accent'
          : 'border-rule bg-surface text-ink-muted hover:text-ink',
      )}
    >
      {children}
    </button>
  )
}

/** Şerit ölçüsü: üstte `etiket/caps` başlık, altında `sayı/orta` değer. */
function Olcum({
  children,
  etiket,
  vurgulu,
}: PropsWithChildren<{ etiket: string; vurgulu?: boolean }>) {
  return (
    <div className="flex items-center gap-2">
      <span className="etiket-caps text-ink-muted">{buyukHarf(etiket)}</span>
      <Sayi className={cn('text-sayi-orta font-semibold', vurgulu ? 'text-signal' : 'text-ink')}>
        {children}
      </Sayi>
    </div>
  )
}

/**
 * Renk açıklaması: bandın kendisi.
 *
 * Üç kutulu kategorik bir lejant artık YANLIŞ olurdu — band sürekli ve
 * kategori yok (İş 3). Gösterilen şey yirmi dört saatlik bandın kendisi ve
 * iki ucunun ne demek olduğudur.
 */
function SaatBandiLejandi() {
  return (
    <span className="flex items-center gap-2 text-sm text-ink-muted">
      <span className="font-mono text-mono-kucuk">00</span>
      <span
        className="h-3.5 w-24 rounded-xs border border-rule"
        style={{
          backgroundImage: `linear-gradient(to right, ${Array.from(
            { length: 24 },
            (_, s) => saatRengi(s),
          ).join(', ')})`,
        }}
        aria-hidden="true"
      />
      <span className="font-mono text-mono-kucuk">24</span>
      <span>saat bandı</span>
    </span>
  )
}

/** Renk açıklaması: 14×14 örnek + adı. */
function Lejant({ children, sinif }: PropsWithChildren<{ sinif: string }>) {
  return (
    <span className="flex items-center gap-2 text-sm text-ink-muted">
      <span className={cn('size-3.5 shrink-0 rounded-xs', sinif)} />
      {children}
    </span>
  )
}


/**
 * Sonuç şeridi — ÖNCE GÜNDELİK DİL, sayı ayrıntının arkasında (SRS FR-6.4).
 *
 * Zorunlu ihlal ile "kabul edilebilir" AYNI ANDA GÖRÜNMEZ: ikisi aynı anda
 * doğru olamaz ve eski ekranda üç ayrı yöne bakan üç işaret vardı.
 */
function SonucSeridi({
  sonuc,
  personelMap,
}: {
  sonuc: DogrulamaSonucu
  personelMap: Map<number, Personel>
}) {
  const [dokumAcik, setDokumAcik] = useState(false)
  const ozet = sonucuOzetle(sonuc)

  return (
    <div className="flex flex-col gap-3">
      <p
        className={cn(
          'm-0 text-sm',
          ozet.tur === 'engellendi' ? 'font-medium text-signal' : 'text-ink',
        )}
      >
        {ozet.cumle}
      </p>

      {ozet.ihlaller.length > 0 && (
        <ul className="m-0 flex list-none flex-col gap-1 p-0">
          {ozet.ihlaller.map((ihlal, i) => (
            <li key={i} className="border-l-2 border-signal pl-3 text-sm text-signal">
              <span className="font-mono">{ihlal.kural_kimlik}</span> — {ihlal.aciklama}
              {ihlal.personel_id !== null && personelMap.get(ihlal.personel_id) && (
                <span className="text-ink-muted">
                  {' '}
                  ({personelMap.get(ihlal.personel_id)!.ad_soyad})
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {ozet.uyarilar.length > 0 && (
        <ul className="m-0 flex list-none flex-col gap-1 p-0">
          {ozet.uyarilar.map((uyari, i) => (
            <li key={i} className="border-l-2 border-rule-strong pl-3 text-sm text-ink-muted">
              {uyari.aciklama}
            </li>
          ))}
        </ul>
      )}

      {ozet.dokum.length > 0 && (
        <div>
          <button
            type="button"
            className="text-sm text-accent underline underline-offset-2"
            aria-expanded={dokumAcik}
            onClick={() => setDokumAcik(!dokumAcik)}
          >
            {dokumAcik ? 'Ceza dökümünü gizle' : 'Ceza dökümünü göster'}
          </button>
          {dokumAcik && (
            <table className="mt-2 w-full border-collapse text-sm">
              <thead>
                <tr className="text-ink-muted">
                  <th className="py-1 text-left font-normal">Hedef</th>
                  <th className="py-1 text-right font-normal">Ham</th>
                  <th className="py-1 text-right font-normal">Ağırlık</th>
                  <th className="py-1 text-right font-normal">Ağırlıklı</th>
                </tr>
              </thead>
              <tbody>
                {ozet.dokum.map((kalem) => (
                  <tr key={kalem.kural_kimlik} className="border-t border-rule">
                    <td className="py-1 text-ink">
                      <span className="font-mono text-ink-muted">{kalem.kural_kimlik}</span>{' '}
                      {kalem.ad}
                    </td>
                    <td className="py-1 text-right">
                      <Sayi>
                        {kalem.ham_fark > 0 ? '+' : ''}
                        {sayiBicimle(kalem.ham_fark, 1)}
                      </Sayi>
                    </td>
                    <td className="py-1 text-right text-ink-muted">
                      <Sayi>{sayiBicimle(kalem.agirlik, 0)}</Sayi>
                    </td>
                    <td className="py-1 text-right">
                      <Sayi>
                        {kalem.agirlikli_fark > 0 ? '+' : ''}
                        {sayiBicimle(kalem.agirlikli_fark, 0)}
                      </Sayi>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
