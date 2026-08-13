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
import { saatRengi } from '../lib/saatRengi'
import { BASLANGIC_SAATLERI, BITIS_SAATLERI, saatiYaz } from '../lib/talepAraligi'
import { saatEtiketi } from '../lib/blok'
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

  // Süzgeçten ÖNCEKİ liste — alttaki "36 personelin 10'u gösteriliyor"
  // satırının paydası budur; süzgeç değiştikçe payda oynamamalı.
  const tumIzgaraPersonelleri = useMemo(() => {
    const idler = new Set(atamalar.map((a) => a.personel_id))
    return [...idler]
      .map((id) => personelMap.get(id))
      .filter((p): p is Personel => p !== undefined)
      .sort((a, b) => a.ad_soyad.localeCompare(b.ad_soyad, 'tr'))
  }, [atamalar, personelMap])

  // Nokta süzgeci personeli DÖNEM BOYUNCA o noktada çalışanlarla sınırlar.
  // Gün bazında daraltmak, günler arasında gezinirken satırların altından
  // kayıp gitmesine yol açardı.
  const noktaPersonelleri = useMemo(() => {
    if (seciliSuzgecNoktaId === null) return null
    return new Set(
      atamalar.filter((a) => a.nokta_id === seciliSuzgecNoktaId).map((a) => a.personel_id),
    )
  }, [atamalar, seciliSuzgecNoktaId])

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
        ? atamalar
        : atamalar.filter((a) => a.nokta_id === seciliSuzgecNoktaId),
    [atamalar, seciliSuzgecNoktaId],
  )

  const atamaIndeksi = useMemo(() => {
    const indeks = new Map<string, Atama>()
    for (const a of atamalar) indeks.set(`${a.personel_id}|${a.tarih}`, a)
    return indeks
  }, [atamalar])

  const atamaBul = (personelId: number, tarih: string): Atama | undefined =>
    atamaIndeksi.get(`${personelId}|${tarih}`)

  const hucreSec = (personelId: number, tarih: string) => {
    setSeciliHucre({ personelId, tarih })
    const mevcut = atamaBul(personelId, tarih)
    setSeciliBaslangic(mevcut ? Number(mevcut.baslangic_zamani.slice(11, 13)) : null)
    setSeciliBitis(mevcut ? bitisSaatiOku(mevcut) : null)
    setSeciliNoktaId(mevcut ? String(mevcut.nokta_id) : BOSALT_DEGERI)
    setDogrulamaSonucu(null)
    setPanelHata(null)
  }

  const istekGovdesiOlustur = (
    ustDeger?: { baslangic: number; bitis: number; noktaId: string },
  ) => {
    if (!seciliHucre || surumId === null) return null
    const bas = ustDeger ? ustDeger.baslangic : seciliBaslangic
    const bit = ustDeger ? ustDeger.bitis : seciliBitis
    const nokta = ustDeger ? ustDeger.noktaId : seciliNoktaId
    return {
      surum_id: surumId,
      personel_id: seciliHucre.personelId,
      tarih: seciliHucre.tarih,
      baslangic_saati: bas === null ? null : saatiYaz(bas),
      bitis_saati: bit === null ? null : saatiYaz(bit),
      nokta_id: nokta === BOSALT_DEGERI ? null : Number(nokta),
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

  /**
   * Sürükleme bırakıldığında (İş 4).
   *
   * Seçim panele yazılır ve DOĞRULAMA İSTEĞİ GÖNDERİLİR — değişiklik
   * uygulanmaz. Sürüklemenin doğrudan yazması, kullanıcının farkında olmadan
   * çizelgeyi değiştirmesi demek olurdu; panel "Uygula" ile arada durur.
   * Görev noktası o günün mevcut bloğundan devralınır (SRS H1: nokta blok
   * boyunca tektir); blok yoksa kullanıcı noktayı seçene kadar doğrulama
   * yapılamaz, çünkü sunucu üçünün birlikte dolu olmasını şart koşar.
   */
  const surukleyerekTanimla = async (personelId: number, baslangic: number, bitis: number) => {
    if (!seciliGun || surumId === null) return
    const mevcut = atamaBul(personelId, seciliGun)
    const noktaId = mevcut ? String(mevcut.nokta_id) : BOSALT_DEGERI
    setSeciliHucre({ personelId, tarih: seciliGun })
    setSeciliBaslangic(baslangic)
    setSeciliBitis(bitis)
    setSeciliNoktaId(noktaId)
    setDogrulamaSonucu(null)
    setPanelHata(null)
    if (noktaId === BOSALT_DEGERI) return

    setPanelYukleniyor(true)
    try {
      const sonuc = await api.atamaDogrula({
        surum_id: surumId,
        personel_id: personelId,
        tarih: seciliGun,
        baslangic_saati: saatiYaz(baslangic),
        bitis_saati: saatiYaz(bitis),
        nokta_id: Number(noktaId),
      })
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
          noktaMap,
        }
      : null

  // Yalnizca taslak ve cozuldu duzenlenebilir; yayinlanmis/arsiv surumde
  // sunucu 409 doner (services/dogrulama_servisi.py).
  const surumDuzenlenebilir =
    surum !== null && (surum.durum === 'taslak' || surum.durum === 'cozuldu')

  // Sunucunun kurali: vardiya ve nokta BIRLIKTE dolu ya da BIRLIKTE bos
  // (schemas/dogrulama.py). Yarim cift 422 doner, o yuzden hic gonderilmez.
  const secimGonderilebilir =
    surumDuzenlenebilir &&
    (seciliBaslangic === null) === (seciliNoktaId === BOSALT_DEGERI) &&
    (seciliBaslangic === null) === (seciliBitis === null)

  const seciliPersonel = seciliHucre ? personelMap.get(seciliHucre.personelId) : null
  const seciliMevcutAtama = seciliHucre ? atamaBul(seciliHucre.personelId, seciliHucre.tarih) : null

  return (
    <AppShell
      aktifEkran="Çizelge"
      donemId={donemId}
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
          <Buton
            varyant="ikincil"
            disabled={disaAktarmaVerisi === null}
            title="Uzun biçim CSV + talep sapması dosyası"
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
        ) : tumIzgaraPersonelleri.length === 0 ? (
          <p className="text-sm text-ink-muted">Bu sürümde henüz atama yok.</p>
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
                onBlokTanimla={surukleyerekTanimla}
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

      {seciliHucre && seciliPersonel && (
        <Kart>
          <KartEtiketi>atama düzenle</KartEtiketi>
          <div className="flex flex-col gap-4">
            <p className="text-sm text-ink">
              {seciliPersonel.ad_soyad} — {gunKisaltmasiVeNumarasi(seciliHucre.tarih)}
            </p>
            <div className="flex flex-wrap items-end gap-4">
              {/* BLOK SEÇİLMEZ, TANIMLANIR (SDD 6.3.3). Gün ızgarasında
                  sürükleyerek de tanımlanır; bu iki alan aynı değeri taşır,
                  sürükleme onları doldurur. */}
              <div className="flex flex-col gap-1">
                <label htmlFor="baslangic-sec" className="text-sm text-ink-muted">
                  Başlangıç
                </label>
                <select
                  id="baslangic-sec"
                  className={SECIM_SINIFI}
                  value={seciliBaslangic === null ? BOSALT_DEGERI : String(seciliBaslangic)}
                  onChange={(e) => {
                    if (e.target.value === BOSALT_DEGERI) {
                      setSeciliBaslangic(null)
                      setSeciliBitis(null)
                      setSeciliNoktaId(BOSALT_DEGERI)
                      return
                    }
                    const saat = Number(e.target.value)
                    setSeciliBaslangic(saat)
                    // Bitiş boşsa asgari blok süresi kadar bir blok önerilir;
                    // değer kural kataloğundan gelir, koda gömülmez (İş 4).
                    if (seciliBitis === null) {
                      const varsayilan = sinirlar.asgariSaat ?? 8
                      setSeciliBitis(((saat + varsayilan - 1) % 24) + 1)
                    }
                  }}
                  disabled={!surumDuzenlenebilir}
                >
                  <option value={BOSALT_DEGERI}>— Boşalt —</option>
                  {BASLANGIC_SAATLERI.map((s) => (
                    <option key={s} value={s}>
                      {saatEtiketi(s)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label htmlFor="bitis-sec" className="text-sm text-ink-muted">
                  Bitiş
                </label>
                <select
                  id="bitis-sec"
                  className={SECIM_SINIFI}
                  value={seciliBitis === null ? BOSALT_DEGERI : String(seciliBitis)}
                  onChange={(e) =>
                    setSeciliBitis(e.target.value === BOSALT_DEGERI ? null : Number(e.target.value))
                  }
                  disabled={!surumDuzenlenebilir || seciliBaslangic === null}
                >
                  <option value={BOSALT_DEGERI}>—</option>
                  {BITIS_SAATLERI.map((s) => (
                    <option key={s} value={s}>
                      {saatEtiketi(s)}
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
                  disabled={!surumDuzenlenebilir || seciliBaslangic === null}
                >
                  <option value={BOSALT_DEGERI}>—</option>
                  {noktalar.map((n) => (
                    <option key={n.nokta_id} value={n.nokta_id}>
                      {n.ad}
                    </option>
                  ))}
                </select>
              </div>
              <Buton
                varyant="ikincil"
                onClick={dogrula}
                disabled={panelYukleniyor || !secimGonderilebilir}
              >
                Doğrula
              </Buton>
              <Buton
                varyant="birincil"
                onClick={uygula}
                disabled={panelYukleniyor || !secimGonderilebilir}
              >
                Uygula
              </Buton>
              {seciliMevcutAtama && (
                <Buton
                  varyant="hayalet"
                  onClick={kilidiDegistir}
                  disabled={panelYukleniyor || !surumDuzenlenebilir}
                >
                  {seciliMevcutAtama.kilitli ? 'Kilidi Aç' : 'Kilitle'}
                </Buton>
              )}
            </div>

            {!surumDuzenlenebilir ? (
              <p className="text-sm text-ink-muted">
                {SURUM_DURUM_METNI[surum?.durum ?? ''] ?? 'Bu'} durumdaki bir sürüm düzenlenemez.
                Değişiklik için Sürümler ekranından taslak türetin.
              </p>
            ) : (
              !secimGonderilebilir && (
                <p className="text-sm text-signal">
                  Çalışma saatleri ve görev noktası birlikte seçilmeli. Hücreyi boşaltmak için
                  başlangıcı “— Boşalt —” yapın.
                </p>
              )
            )}

            {panelHata && <p className="text-sm text-signal">{panelHata}</p>}

            {dogrulamaSonucu && (
              <div>
                <p className="text-sm text-ink">
                  {dogrulamaSonucu.kabul_edilebilir
                    ? 'Kabul edilebilir.'
                    : 'Zorunlu kısıt ihlali — reddedildi.'}{' '}
                  Ceza değişimi:{' '}
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

                {dogrulamaSonucu.uyarilar.length > 0 && (
                  <ul className="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                    {dogrulamaSonucu.uyarilar.map((uyari, i) => (
                      <li key={i} className="border-l-2 border-signal pl-3 text-sm text-signal">
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
