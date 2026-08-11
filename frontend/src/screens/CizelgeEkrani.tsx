import { useEffect, useMemo, useState, type PropsWithChildren } from 'react'
import { api, ApiHatasi } from '../api/client'
import type {
  Atama,
  CizelgeSurumu,
  Donem,
  DogrulamaSonucu,
  GorevNoktasi,
  FazlaKadro,
  KapsamaAcigi,
  Personel,
  VardiyaTipi,
  Yetkinlik,
  Analiz,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { YazdirmaOnizlemesi } from '../components/YazdirmaOnizlemesi'
import { csvDisaAktar, type CizelgeVerisi } from '../lib/disaAktarma'
import { Buton, Kart, KartEtiketi, Sayi } from '../components/app-ui'
import { cn } from '../lib/utils'
import { belirtmeHaliEki, buyukHarf, kisalt } from '../lib/metin'
import { sayiBicimle } from '../lib/sayi'
import {
  bugunIso,
  donemAraligiBicimle,
  gunBasligiParcalari,
  gunKisaltmasiVeNumarasi,
  gunlerListesi,
  haftaSonuMu,
  tarihBicimle,
} from '../lib/tarih'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
  yenidenCozIste: (donemId: number) => void
}

const BOSALT_DEGERI = ''

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

type Gorunum = 'personel' | 'nokta'

// --- Izgara olculeri (Tasarim Referansi surum 4) -------------------------
// Ad sutunu dokumanin degerinde: 220px. Surum 3'te 180px'ti ve tek satirda
// yalnizca adi tasiyordu; artik ad ve sicil alt alta duruyor.
const AD_SUTUNU = 'w-[220px] min-w-[220px] max-w-[220px]'
// Gun sutunu ASGARI 60px, ustu serbest. Dokuman 128px diyor ve 7 gunluk
// Figma cercevesinde 220 + 7x128 = 1116px, yani kartin tamami. Sabit 128px
// vermek 28 gunluk donemde (kabul kriteri olcegi) tabloyu ~3800px yapardi;
// bunun yerine tablo `w-full` ile kabi doldurur: 7 gunde sutunlar
// kendiliginden ~128px'e acilir, 28 gunde 60px'te kalip yatay kayar. Tek
// kural iki ucu da karsilar.
const GUN_SUTUNU = 'min-w-[60px]'

// --- Satir yukseklikleri (surum 4) ---------------------------------------
// Ucu de dokumanin degerinde, cunku artik uc satirin da icerigi iki
// satirlik: gun basligi (kisaltma + 28px'lik bugun dairesi), personel
// hucresi (ad + sicil) ve gun hucresi (vardiya + nokta kisaltmasi).
const BASLIK_SATIRI = 'h-[54px]' // 32 -> 54
const KAPSAMA_SERIDI = 'h-[46px]' // yeni
const HUCRE_YUKSEKLIGI = 'h-[46px]' // 28 -> 46

// Kaydirilabilir alanin yuksekligi: ust cubuk (64) + icerik dolgusu (56) +
// secim karti (~140) + kart araligi (20). Izgara kendi icinde kaydigi icin
// yapiskan baslik satiri gorunur kalir. Surum 4'te baslik ve satirlar
// buyudugu icin pay 280 -> 292.
const IZGARA_YUKSEKLIGI = 'max-h-[calc(100svh-292px)]'

// Vardiya kodlaması yalnızca Çizelge ızgarasında kullanılır (TASARIM_REFERANSI.md):
// gündüz soluk sıcak (#E9E7D9 — sürüm 4'te beyazdan çıkarıldı, boş hücreden
// ayrılsın diye), akşam sage, gece koyu — vardiya tipinin kendisi bunu
// taşımadığından (yalnızca gece_mi var) başlangıç saatinden yaklaştırılır.
function vardiyaHucreSinifi(vardiya: VardiyaTipi | undefined): string {
  if (!vardiya) return 'bg-surface'
  if (vardiya.gece_mi) return 'bg-vardiya-gece text-vardiya-gece-ink'
  const saat = Number(vardiya.baslangic_saati.slice(0, 2))
  return saat >= 14 ? 'bg-vardiya-aksam text-ink' : 'bg-vardiya-gunduz text-ink'
}

export function CizelgeEkrani({ ekranSec, donemId, donemIdSec, yenidenCozIste }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [surumId, setSurumId] = useState<number | null>(null)

  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])
  const [noktalar, setNoktalar] = useState<GorevNoktasi[]>([])

  const [atamalar, setAtamalar] = useState<Atama[]>([])
  const [kapsamaAcigi, setKapsamaAcigi] = useState<KapsamaAcigi[]>([])
  const [fazlaKadro, setFazlaKadro] = useState<FazlaKadro[]>([])
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const [yetkinlikler, setYetkinlikler] = useState<Yetkinlik[]>([])
  const [analiz, setAnaliz] = useState<Analiz | null>(null)
  // Süzgeçler (Tasarım Referansı v4, Çizelge ekranı). İkisi de YALNIZCA
  // görünümü daraltır; hiçbir atamayı değiştirmez ve sunucuya gitmez —
  // veri zaten sürümle birlikte tamamı yüklü.
  const [seciliYetkinlikId, setSeciliYetkinlikId] = useState<number | null>(null)
  const [yalnizcaAcik, setYalnizcaAcik] = useState(false)

  const [gorunum, setGorunum] = useState<Gorunum>('personel')
  const [yazdirmaAcik, setYazdirmaAcik] = useState(false)
  const [seciliHucre, setSeciliHucre] = useState<SeciliHucre | null>(null)
  const [seciliVardiyaTipiId, setSeciliVardiyaTipiId] = useState<string>(BOSALT_DEGERI)
  const [seciliNoktaId, setSeciliNoktaId] = useState<string>(BOSALT_DEGERI)
  const [dogrulamaSonucu, setDogrulamaSonucu] = useState<DogrulamaSonucu | null>(null)
  const [panelYukleniyor, setPanelYukleniyor] = useState(false)
  const [panelHata, setPanelHata] = useState<string | null>(null)

  // Tanim listeleri + donemler: bir kez yuklenir.
  useEffect(() => {
    Promise.all([
      api.donemler(),
      api.personelListele(),
      api.vardiyaTipiListele(),
      api.noktaListele(),
      api.yetkinlikListele(),
    ])
      .then(([d, p, v, n, y]) => {
        setDonemler(d)
        setPersonelListesi(p)
        setVardiyaTipleri(v)
        setNoktalar(n)
        setYetkinlikler(y.filter((k) => k.aktif))
        if (donemId === null && d[0]) donemIdSec(d[0].donem_id)
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

  const donem = donemler.find((d) => d.donem_id === donemId) ?? null
  const surum = surumler.find((s) => s.surum_id === surumId) ?? null

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )
  const vardiyaMap = useMemo(
    () => new Map(vardiyaTipleri.map((v) => [v.vardiya_tipi_id, v])),
    [vardiyaTipleri],
  )
  const noktaMap = useMemo(() => new Map(noktalar.map((n) => [n.nokta_id, n])), [noktalar])

  const donemGunleri = useMemo(
    () => (donem ? gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi) : []),
    [donem],
  )
  // Bugun isareti icin: bileşen saat OKUMAZ demek burada gecerli degil —
  // isaret tanimi geregi "su anki gun"e bagli. lib/tarih.ts'ten gecer.
  const bugun = bugunIso()

  // Şeridin basamakları GÖREV NOKTALARIDIR — gün başına biri, her zaman aynı
  // sırada (TASARIM_REFERANSI.md: "Kapsama şeridinde karşılanan NOKTALAR
  // nötr gri, yalnızca açık olanlar turuncudur").
  //
  // Sıranın sabit olması şeridin bütün işidir: turuncunun kaçıncı basamakta
  // olduğu HANGİ noktanın açık verdiğini söyler. Açıkları sona toplamak
  // şeridi bir sayaca indirger ve tek tek basamakları anlamsızlaştırır.
  const seritNoktalari = useMemo(
    () => noktalar.filter((n) => n.aktif).sort((a, b) => a.nokta_id - b.nokta_id),
    [noktalar],
  )

  // Tarih → o gün açık veren nokta kimlikleri. Bir nokta o günün herhangi bir
  // vardiyasında eksik kaldıysa basamağı turuncudur; şerit vardiya kırılımına
  // inmez, o ayrım ızgaranın kendi hücrelerinde zaten görünür.
  const acikNoktalar = useMemo(() => {
    const indeks = new Map<string, Map<number, number>>()
    for (const k of kapsamaAcigi) {
      let gun = indeks.get(k.tarih)
      if (!gun) {
        gun = new Map()
        indeks.set(k.tarih, gun)
      }
      gun.set(k.nokta_id, (gun.get(k.nokta_id) ?? 0) + k.eksik_sayi)
    }
    return indeks
  }, [kapsamaAcigi])

  const gunler = useMemo(
    () => (yalnizcaAcik ? donemGunleri.filter((g) => acikNoktalar.has(g)) : donemGunleri),
    [donemGunleri, yalnizcaAcik, acikNoktalar],
  )

  // Süzgeçten ÖNCEKİ liste — alttaki "36 personelin 10'u gösteriliyor"
  // satırının paydası budur; süzgeç değiştikçe payda oynamamalı.
  const tumIzgaraPersonelleri = useMemo(() => {
    const idler = new Set(atamalar.map((a) => a.personel_id))
    return [...idler]
      .map((id) => personelMap.get(id))
      .filter((p): p is Personel => p !== undefined)
      .sort((a, b) => a.ad_soyad.localeCompare(b.ad_soyad, 'tr'))
  }, [atamalar, personelMap])

  const izgaraPersonelleri = useMemo(
    () =>
      seciliYetkinlikId === null
        ? tumIzgaraPersonelleri
        : tumIzgaraPersonelleri.filter((p) => p.yetkinlik_idleri.includes(seciliYetkinlikId)),
    [tumIzgaraPersonelleri, seciliYetkinlikId],
  )

  // Izgara hucre basina arama yapar; 36 personel x 28 gun = 1008 hucrenin her
  // birinde atama listesini bastan taramak (dogrusal arama) 28 gunluk donemde
  // gorunur gecikme yaratiyordu. Uc indeks bir kez kurulur.
  const atamaIndeksi = useMemo(() => {
    const indeks = new Map<string, Atama>()
    for (const a of atamalar) indeks.set(`${a.personel_id}|${a.tarih}`, a)
    return indeks
  }, [atamalar])

  const noktaIndeksi = useMemo(() => {
    const indeks = new Map<string, Atama[]>()
    for (const a of atamalar) {
      const anahtar = `${a.tarih}|${a.vardiya_tipi_id}|${a.nokta_id}`
      const mevcut = indeks.get(anahtar)
      if (mevcut) mevcut.push(a)
      else indeks.set(anahtar, [a])
    }
    return indeks
  }, [atamalar])

  const kapsamaIndeksi = useMemo(() => {
    const indeks = new Map<string, KapsamaAcigi>()
    for (const k of kapsamaAcigi) {
      indeks.set(`${k.tarih}|${k.vardiya_tipi_id}|${k.nokta_id}`, k)
    }
    return indeks
  }, [kapsamaAcigi])

  const atamaBul = (personelId: number, tarih: string): Atama | undefined =>
    atamaIndeksi.get(`${personelId}|${tarih}`)

  const kapsamaBul = (atama: Atama): KapsamaAcigi | undefined =>
    kapsamaIndeksi.get(`${atama.tarih}|${atama.vardiya_tipi_id}|${atama.nokta_id}`)

  // Nokta gorunumunun satirlari (SDD 6.3.3). Talep nokta VE vardiya kiriliminda
  // tanimli oldugundan (SDD 4.2.1 talep) satir ekseni de bu ikilidir; yalniz
  // nokta satiri, uc vardiyayi tek hucrede toplamak zorunda kalirdi.
  const noktaSatirlari = useMemo(
    () =>
      noktalar.flatMap((n) =>
        vardiyaTipleri.map((v) => ({ nokta: n, vardiya: v })),
      ),
    [noktalar, vardiyaTipleri],
  )

  const hucreSec = (personelId: number, tarih: string) => {
    setSeciliHucre({ personelId, tarih })
    const mevcut = atamaBul(personelId, tarih)
    setSeciliVardiyaTipiId(mevcut ? String(mevcut.vardiya_tipi_id) : BOSALT_DEGERI)
    setSeciliNoktaId(mevcut ? String(mevcut.nokta_id) : BOSALT_DEGERI)
    setDogrulamaSonucu(null)
    setPanelHata(null)
  }

  const istekGovdesiOlustur = () => {
    if (!seciliHucre || surumId === null) return null
    return {
      surum_id: surumId,
      personel_id: seciliHucre.personelId,
      tarih: seciliHucre.tarih,
      vardiya_tipi_id: seciliVardiyaTipiId === BOSALT_DEGERI ? null : Number(seciliVardiyaTipiId),
      nokta_id: seciliNoktaId === BOSALT_DEGERI ? null : Number(seciliNoktaId),
    }
  }

  const dogrula = async () => {
    const govde = istekGovdesiOlustur()
    if (!govde) return
    setPanelYukleniyor(true)
    setPanelHata(null)
    try {
      const sonuc = await api.atamaDogrula(govde)
      setDogrulamaSonucu(sonuc)
    } catch (e) {
      setPanelHata(e instanceof Error ? e.message : 'Doğrulama başarısız')
    } finally {
      setPanelYukleniyor(false)
    }
  }

  const uygula = async () => {
    const govde = istekGovdesiOlustur()
    if (!govde) return
    setPanelYukleniyor(true)
    setPanelHata(null)
    try {
      const sonuc = await api.atamaGuncelle(govde)
      setDogrulamaSonucu(sonuc)
      surumYukle()
    } catch (e) {
      if (e instanceof ApiHatasi && e.detay && typeof e.detay === 'object') {
        setDogrulamaSonucu(e.detay as DogrulamaSonucu)
      } else {
        setPanelHata(e instanceof Error ? e.message : 'Değişiklik uygulanamadı')
      }
    } finally {
      setPanelYukleniyor(false)
    }
  }

  const kilidiDegistir = async () => {
    if (!seciliHucre || surumId === null) return
    const mevcut = atamaBul(seciliHucre.personelId, seciliHucre.tarih)
    if (!mevcut) return
    setPanelYukleniyor(true)
    setPanelHata(null)
    try {
      await api.atamaKilitAyarla(surumId, seciliHucre.personelId, seciliHucre.tarih, !mevcut.kilitli)
      surumYukle()
    } catch (e) {
      setPanelHata(e instanceof Error ? e.message : 'Kilit değiştirilemedi')
    } finally {
      setPanelYukleniyor(false)
    }
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
          vardiyaMap,
          noktaMap,
        }
      : null

  const seciliPersonel = seciliHucre ? personelMap.get(seciliHucre.personelId) : null
  const seciliMevcutAtama = seciliHucre ? atamaBul(seciliHucre.personelId, seciliHucre.tarih) : null

  return (
    <AppShell
      aktifEkran="Çizelge"
      donemId={donemId}
      ekranSec={ekranSec}
      baslik="Çizelge"
      altBaslik={
        // `etiket/mono-caps` — durum ve sürüm numarası veri, cümle değil.
        surum ? (
          <span className="mono-caps rounded-sm bg-sunken px-2 py-1 text-ink-muted">
            {buyukHarf(SURUM_DURUM_METNI[surum.durum] ?? surum.durum)} · SÜRÜM{' '}
            {surum.surum_no}
          </span>
        ) : undefined
      }
      aksiyonlar={
        <>
          {/* SDD 6.3.3 Görünüm Anahtarı: ızgarayı personel ekseninden görev
              noktası eksenine çevirir ve geri alır. Sürüm 4'te tek bir
              değiştirme butonu değil, iki durumu da gösteren bir ikili
              anahtar — hangi eksende olunduğu butona bakmadan görünür. */}
          <div className="flex rounded-sm bg-chrome-raised p-0.5">
            {(['personel', 'nokta'] as const).map((secenek) => (
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
                {secenek === 'personel' ? 'Personel' : 'Nokta'}
              </button>
            ))}
          </div>
          <Buton
            varyant="ikincil"
            disabled={disaAktarmaVerisi === null}
            title="Uzun biçim CSV + kapsama açığı dosyası"
            onClick={() => disaAktarmaVerisi && csvDisaAktar(disaAktarmaVerisi)}
          >
            CSV
          </Buton>
          <Buton
            varyant="ikincil"
            disabled={disaAktarmaVerisi === null}
            title="Personel × gün matrisi, yatay A4"
            onClick={() => setYazdirmaAcik(true)}
          >
            Yazdır
          </Buton>
          <Buton
            varyant="birincil"
            disabled={donemId === null}
            onClick={() => donemId !== null && yenidenCozIste(donemId)}
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
        </div>
      </Kart>

      {hata && <p className="text-sm text-signal">{hata}</p>}

      {/* Süzgeç ve ölçüm şeridi (Tasarım Referansı v4, Çizelge ekranı).
          Solda ızgarayı daraltan süzgeçler, sağda sürümün üç ölçüsü —
          ikisi de aynı satırda durur çünkü "neyi görüyorum" ile "ne kadarı
          karşılandı" aynı anda okunması gereken iki bilgidir. */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-rule pb-4">
        <span className="etiket-caps text-ink-muted">{buyukHarf('Yetkinlik')}</span>
        <div className="flex flex-wrap items-center gap-2">
          <SuzgecCipi
            secili={seciliYetkinlikId === null}
            onSec={() => setSeciliYetkinlikId(null)}
          >
            Tümü
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
        ) : tumIzgaraPersonelleri.length === 0 ? (
          <p className="text-sm text-ink-muted">Bu sürümde henüz atama yok.</p>
        ) : /* Süzgeçlerin ikisi de listeyi boşaltabilir. "Atama yok" demek
              yanlış olurdu — atama var, süzgeç saklıyor; kullanıcı süzgeci
              geri almadan bunu anlayamaz. */
        gunler.length === 0 ? (
          <p className="text-sm text-ink-muted">
            Bu dönemde açık verilen gün yok. Süzgeci kaldırarak tüm günleri görebilirsiniz.
          </p>
        ) : izgaraPersonelleri.length === 0 ? (
          <p className="text-sm text-ink-muted">
            Seçili yetkinlikte bu sürüme atanmış personel yok.
          </p>
        ) : (
          // Kaydirma kabi: yatay VE dikey. Yapiskan hucreler konumlarini bu
          // kaba gore alir, o yuzden yukseklik sinirli olmak zorunda — sinirsiz
          // yukseklikte kap hic dikey kaymaz ve `sticky top-0` etkisiz kalir.
          // border-separate: border-collapse ile yapiskan hucrelerin kenarligi
          // kaydirma sirasinda tabloda kalip hucreyle birlikte gitmiyor.
          <div className={cn('relative overflow-auto', IZGARA_YUKSEKLIGI)}>
            <table className="w-full min-w-max border-separate border-spacing-0">
              <thead>
                <tr>
                  <th
                    className={cn(
                      'mono-caps sticky top-0 left-0 z-30 border-b border-r border-rule bg-surface px-3 text-left text-ink-muted',
                      AD_SUTUNU,
                    )}
                  >
                    {buyukHarf(gorunum === 'personel' ? 'Personel' : 'Görev Noktası')}
                  </th>
                  {gunler.map((gun) => {
                    const { kisaltma, numara } = gunBasligiParcalari(gun)
                    const bugunMu = gun === bugun
                    return (
                      <th
                        key={gun}
                        className={cn(
                          'sticky top-0 z-20 border-b border-rule bg-surface text-center font-mono text-mono-kucuk font-medium whitespace-nowrap text-ink-muted',
                          BASLIK_SATIRI,
                          GUN_SUTUNU,
                          haftaSonuMu(gun) && 'bg-sunken',
                        )}
                      >
                        <span className="flex flex-col items-center justify-center gap-0.5">
                          <span>{kisaltma}</span>
                          {/* Bugün işareti: 28px tam yuvarlak accent daire,
                              içinde chrome-ink metin. Takvimlerden tanıdık
                              olduğu için açıklama gerektirmez. Yalnızca bugün
                              bu dönem içindeyse çizilir — `gunler` zaten
                              dönemin günleri olduğundan kıyas yeterlidir. */}
                          <span
                            className={cn(
                              'flex size-7 items-center justify-center font-semibold',
                              bugunMu
                                ? 'rounded-full bg-accent text-chrome-ink'
                                : 'text-ink',
                            )}
                          >
                            {numara}
                          </span>
                        </span>
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody>
                {/* Kapsama şeridi — başlığın hemen altında, personel
                    satırlarının üstünde. Her basamak o günün bir (nokta ×
                    vardiya) talebi; karşılanan nötr gri, açık olan turuncu.
                    Nokta görünümünde çizilmez: orada açık zaten satırın
                    kendi hücresinde görünür ve şerit onu ikinci kez söyler. */}
                {gorunum === 'personel' && (
                  <tr>
                    <td
                      className={cn(
                        'etiket-caps sticky left-0 z-10 border-b border-r border-rule bg-surface px-3 text-ink-muted',
                        KAPSAMA_SERIDI,
                        AD_SUTUNU,
                      )}
                      // Basamak sırası sabittir ve anlam taşır; sıranın hangi
                      // noktalara karşılık geldiği başlıktan okunur.
                      title={`Basamak sırası: ${seritNoktalari.map((n) => n.ad).join(' · ')}`}
                    >
                      {buyukHarf('Kapsama')}
                    </td>
                    {gunler.map((gun) => {
                      const gunAciklari = acikNoktalar.get(gun)
                      return (
                        <td
                          key={gun}
                          className={cn(
                            'border-b border-rule px-1.5',
                            KAPSAMA_SERIDI,
                            GUN_SUTUNU,
                            haftaSonuMu(gun) && 'bg-sunken',
                          )}
                        >
                          <span className="flex items-center justify-center gap-1">
                            {seritNoktalari.map((n) => {
                              const eksik = gunAciklari?.get(n.nokta_id) ?? 0
                              return (
                                // Her basamak tek başına okunabilir olmalı:
                                // şeridin tamamına değil, basamağın KENDİSİNE
                                // başlık verilir — imleç turuncunun üstüne
                                // geldiğinde hangi nokta olduğunu söyler.
                                <span
                                  key={n.nokta_id}
                                  title={`${tarihBicimle(gun)} · ${n.ad} — ${
                                    eksik > 0 ? `${eksik} kişi eksik` : 'karşılandı'
                                  }`}
                                  className={cn(
                                    'h-1.5 flex-1 rounded-xs',
                                    eksik > 0 ? 'bg-signal' : 'bg-rule-strong',
                                  )}
                                />
                              )
                            })}
                          </span>
                        </td>
                      )
                    })}
                  </tr>
                )}
                {gorunum === 'personel'
                  ? izgaraPersonelleri.map((p) => (
                      <tr key={p.personel_id}>
                        {/* Ad ve sicil alt alta, sola dayalı (Tasarım
                            Referansı v4). Sicil ayırt edicidir: aynı adı
                            taşıyan iki personel ızgarada yalnız adla
                            ayrılamıyordu. */}
                        <td
                          className={cn(
                            'sticky left-0 z-10 border-b border-r border-rule bg-surface px-3 text-left',
                            AD_SUTUNU,
                          )}
                          title={`${p.ad_soyad} · ${p.sicil_no}`}
                        >
                          <span className="block truncate text-sm text-ink">{p.ad_soyad}</span>
                          <span className="block truncate font-mono text-mono-kucuk text-ink-muted">
                            {p.sicil_no}
                          </span>
                        </td>
                        {gunler.map((gun) => {
                          const atama = atamaBul(p.personel_id, gun)
                          const kapsama = atama ? kapsamaBul(atama) : undefined
                          const vardiya = atama ? vardiyaMap.get(atama.vardiya_tipi_id) : undefined
                          const nokta = atama ? noktaMap.get(atama.nokta_id) : undefined
                          const seciliMi =
                            seciliHucre?.personelId === p.personel_id && seciliHucre?.tarih === gun
                          return (
                            <td
                              key={gun}
                              className={cn(
                                'border-b border-rule p-0',
                                GUN_SUTUNU,
                                haftaSonuMu(gun) && 'bg-sunken',
                              )}
                            >
                              {/* Vardiya rengi hücrenin KENDİ dolgusudur
                                  (TASARIM_REFERANSI.md): buton hücreyi tam
                                  doldurur, içeride küçük bir renkli kutu
                                  durmaz. Kısaltmalar alt alta — tek satırda
                                  "GEC GÜV" Azeret Mono 11,5px ile 52,3px
                                  sürüyor ve 60px'lik sütuna sığmıyordu. */}
                              <button
                                type="button"
                                className={cn(
                                  'box-border flex w-full flex-col items-center justify-center leading-tight font-mono text-mono-kucuk',
                                  HUCRE_YUKSEKLIGI,
                                  // Bos hucre: kenarlik ve zemin yok — goz yalniz
                                  // dolu hucreleri gorur, 28 gunluk izgarada
                                  // bosluklar arka plana cekilir.
                                  atama && !kapsama && vardiyaHucreSinifi(vardiya),
                                  kapsama && 'bg-signal-soft font-medium text-signal',
                                  atama?.kilitli && 'outline-2 outline-offset-[-2px] outline-accent',
                                  seciliMi && 'ring-2 ring-inset ring-ink',
                                )}
                                onClick={() => hucreSec(p.personel_id, gun)}
                                title={
                                  atama
                                    ? `${p.ad_soyad} — ${tarihBicimle(gun)} · ${vardiya?.ad ?? ''} · ${nokta?.ad ?? ''}${kapsama ? ` · ${kapsama.eksik_sayi} kişi eksik` : ''}`
                                    : `${p.ad_soyad} — ${tarihBicimle(gun)} · atama yok`
                                }
                              >
                                {atama &&
                                  (kapsama ? (
                                    <span className="font-semibold">−{kapsama.eksik_sayi}</span>
                                  ) : (
                                    <>
                                      <span className="font-semibold">
                                        {kisalt(vardiya?.ad ?? '')}
                                      </span>
                                      <span className="opacity-80">{kisalt(nokta?.ad ?? '')}</span>
                                    </>
                                  ))}
                              </button>
                            </td>
                          )
                        })}
                      </tr>
                    ))
                  : noktaSatirlari.map(({ nokta, vardiya }) => (
                      <tr key={`${nokta.nokta_id}-${vardiya.vardiya_tipi_id}`}>
                        <td
                          className={cn(
                            'sticky left-0 z-10 border-b border-r border-rule bg-surface px-3 text-left',
                            AD_SUTUNU,
                          )}
                          title={`${nokta.ad} — ${vardiya.ad}`}
                        >
                          <span className="block truncate text-sm text-ink">{nokta.ad}</span>
                          <span className="block truncate font-mono text-mono-kucuk text-ink-muted">
                            {kisalt(vardiya.ad)}
                          </span>
                        </td>
                        {gunler.map((gun) => {
                          const anahtar = `${gun}|${vardiya.vardiya_tipi_id}|${nokta.nokta_id}`
                          const hucreAtamalari = noktaIndeksi.get(anahtar) ?? []
                          const kapsama = kapsamaIndeksi.get(anahtar)
                          return (
                            <td
                              key={gun}
                              className={cn(
                                'border-b border-rule p-0.5 align-top',
                                GUN_SUTUNU,
                                haftaSonuMu(gun) && 'bg-sunken',
                              )}
                            >
                              {/* SDD 6.3.3: nokta gorunumunde hucre, o vardiyaya
                                  atanan personeldir. Ad yerine sicil yazilir —
                                  yedi kisilik bir Guvenlik hucresi tam adlarla
                                  sutuna sigmaz; sicil zaten kisa ve tekildir. */}
                              <div
                                className={cn(
                                  'flex flex-col gap-px rounded-sm px-1 py-0.5 font-mono text-mono-kucuk leading-tight',
                                  hucreAtamalari.length > 0 && vardiyaHucreSinifi(vardiya),
                                  hucreAtamalari.length > 0 && 'border border-rule',
                                  kapsama && 'border-signal',
                                )}
                                title={
                                  hucreAtamalari.length === 0
                                    ? `${nokta.ad} — ${vardiya.ad} · ${tarihBicimle(gun)} · atama yok`
                                    : `${nokta.ad} — ${vardiya.ad} · ${tarihBicimle(gun)}\n${hucreAtamalari
                                        .map((a) => personelMap.get(a.personel_id)?.ad_soyad ?? '')
                                        .join('\n')}`
                                }
                              >
                                {hucreAtamalari.map((a) => (
                                  <span key={a.atama_id} className="truncate">
                                    {personelMap.get(a.personel_id)?.sicil_no ?? '—'}
                                  </span>
                                ))}
                                {kapsama && (
                                  <span className="font-medium text-signal">
                                    −{kapsama.eksik_sayi}
                                  </span>
                                )}
                              </div>
                            </td>
                          )
                        })}
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Izgara altı: solda ne kadarının gösterildiği, sağda renk
            açıklaması. Bu satır DÜZ CÜMLEDİR ve Mono değildir — Azeret Mono
            yalnızca sayı ve koda ayrılmıştır (TASARIM_REFERANSI.md). */}
        {!yukleniyor && izgaraPersonelleri.length > 0 && gorunum === 'personel' && (
          <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink-muted">
            <span>
              <Sayi>{sayiBicimle(tumIzgaraPersonelleri.length)}</Sayi> personelin{' '}
              <Sayi>{sayiBicimle(izgaraPersonelleri.length)}</Sayi>
              {belirtmeHaliEki(izgaraPersonelleri.length)} gösteriliyor · yetkinlik süzgeci:{' '}
              {seciliYetkinlikId === null
                ? 'tümü'
                : (yetkinlikler.find((y) => y.yetkinlik_id === seciliYetkinlikId)?.ad ?? 'tümü')}
              {yalnizcaAcik && ' · yalnızca açık verilen günler'}
            </span>
            <div className="ml-auto flex flex-wrap items-center gap-4">
              <Lejant sinif="bg-vardiya-gunduz border border-rule">Gündüz</Lejant>
              <Lejant sinif="bg-vardiya-aksam border border-rule">Akşam</Lejant>
              <Lejant sinif="bg-vardiya-gece">Gece</Lejant>
              <Lejant sinif="border-2 border-accent bg-surface">Kilitli</Lejant>
              <Lejant sinif="bg-signal">Açık</Lejant>
            </div>
          </div>
        )}
      </Kart>

      {seciliHucre && seciliPersonel && (
        <Kart>
          <KartEtiketi>atama düzenle</KartEtiketi>
          <div className="flex flex-col gap-4">
            <p className="text-sm text-ink">
              {seciliPersonel.ad_soyad} — {gunKisaltmasiVeNumarasi(seciliHucre.tarih)}
            </p>
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="vardiya-sec" className="text-sm text-ink-muted">
                  Vardiya
                </label>
                <select
                  id="vardiya-sec"
                  className={SECIM_SINIFI}
                  value={seciliVardiyaTipiId}
                  onChange={(e) => setSeciliVardiyaTipiId(e.target.value)}
                >
                  <option value={BOSALT_DEGERI}>— Boşalt —</option>
                  {vardiyaTipleri.map((v) => (
                    <option key={v.vardiya_tipi_id} value={v.vardiya_tipi_id}>
                      {v.ad}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label htmlFor="nokta-sec" className="text-sm text-ink-muted">
                  Görev Noktası
                </label>
                <select
                  id="nokta-sec"
                  className={SECIM_SINIFI}
                  value={seciliNoktaId}
                  onChange={(e) => setSeciliNoktaId(e.target.value)}
                  disabled={seciliVardiyaTipiId === BOSALT_DEGERI}
                >
                  <option value={BOSALT_DEGERI}>—</option>
                  {noktalar.map((n) => (
                    <option key={n.nokta_id} value={n.nokta_id}>
                      {n.ad}
                    </option>
                  ))}
                </select>
              </div>
              <Buton varyant="ikincil" onClick={dogrula} disabled={panelYukleniyor}>
                Doğrula
              </Buton>
              <Buton varyant="birincil" onClick={uygula} disabled={panelYukleniyor}>
                Uygula
              </Buton>
              {seciliMevcutAtama && (
                <Buton varyant="hayalet" onClick={kilidiDegistir} disabled={panelYukleniyor}>
                  {seciliMevcutAtama.kilitli ? 'Kilidi Aç' : 'Kilitle'}
                </Buton>
              )}
            </div>

            {panelHata && <p className="text-sm text-signal">{panelHata}</p>}

            {dogrulamaSonucu && (
              <div>
                <p className="text-sm text-ink">
                  {dogrulamaSonucu.kabul_edilebilir
                    ? 'Kabul edilebilir.'
                    : 'Zorunlu kısıt ihlali — reddedildi.'}{' '}
                  Ceza değişimi:{' '}
                  {/* AĞIRLIKLI değer gösterilir. Ham toplam farklı birimleri
                      (kişi, vardiya, saat, gün) ağırlıksız topluyordu; kapsama
                      açığı (w1) ile vardiya deseni değişimi (w6) ekranda aynı
                      büyüklükte görünüyordu. */}
                  <Sayi>
                    {dogrulamaSonucu.agirlikli_ceza_degisimi > 0 ? '+' : ''}
                    {sayiBicimle(dogrulamaSonucu.agirlikli_ceza_degisimi, 0)}
                  </Sayi>
                </p>

                {dogrulamaSonucu.zorunlu_ihlaller.length > 0 && (
                  <ul className="m-0 mt-1 flex list-none flex-col gap-1 p-0">
                    {dogrulamaSonucu.zorunlu_ihlaller.map((ihlal, i) => (
                      <li key={i} className="text-sm text-signal">
                        {ihlal.kural_kimlik} — {ihlal.aciklama}
                      </li>
                    ))}
                  </ul>
                )}

                {/* Değişikliğin NEREDE ne yaptığı. Bunlar zorunlu ihlal değil:
                    değişiklik uygulanır, karar kullanıcıya bırakılır (SDD 5.5).
                    Ama bir sayı olarak değil, cümle olarak görünmeleri gerekir —
                    "+1000" kimseye Vardiya Şefliği'nin açıkta kaldığını söylemez. */}
                {dogrulamaSonucu.uyarilar.length > 0 && (
                  <ul className="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    {dogrulamaSonucu.uyarilar.map((uyari, i) => (
                      <li
                        key={i}
                        className="border-l-2 border-signal pl-3 text-sm text-signal"
                      >
                        {uyari.aciklama}
                      </li>
                    ))}
                  </ul>
                )}

                {dogrulamaSonucu.ceza_dokumu.length > 0 && (
                  <table className="mt-3 w-full border-collapse text-sm">
                    <thead>
                      <tr className="text-ink-muted">
                        <th className="py-1 text-left font-normal">Hedef</th>
                        <th className="py-1 text-right font-normal">Ham</th>
                        <th className="py-1 text-right font-normal">Ağırlık</th>
                        <th className="py-1 text-right font-normal">Ağırlıklı</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dogrulamaSonucu.ceza_dokumu.map((kalem) => (
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
        </Kart>
      )}
    </AppShell>
  )
}

/**
 * Süzgeç çipi — Tanımlar sekme çubuğuyla aynı dil: aktif `accent-soft`
 * zemin + `accent` metin, pasif zeminsiz + `ink-muted` (TASARIM_REFERANSI.md,
 * "Sekme çubuğu"). Ayrı bir bileşen, çünkü yetkinlik listesi veriden gelir ve
 * çip sayısı sabit değildir.
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

/** Renk açıklaması: 14×14 örnek + adı. */
function Lejant({ children, sinif }: PropsWithChildren<{ sinif: string }>) {
  return (
    <span className="flex items-center gap-2 text-sm text-ink-muted">
      <span className={cn('size-3.5 shrink-0 rounded-xs', sinif)} />
      {children}
    </span>
  )
}
