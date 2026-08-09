import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type {
  Bina,
  GorevNoktasi,
  GunTipi,
  Kural,
  Personel,
  TalepHucresi,
  TanimYolu,
  VardiyaTipi,
  Yetkinlik,
  YukGostergesi,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import {
  SilmeOnayi,
  TanimListesi,
  gorunumKur,
  type TanimGorunumu,
} from '../components/TanimYonetimi'
import { Buton, Kart, KartEtiketi, Rozet, Sayi } from '../components/app-ui'
import { Input } from '@/components/ui/input'
import { cn } from '../lib/utils'
import { bugunIso } from '../lib/tarih'
import {
  digerEsnekAgirlikToplami,
  s1BaskinligiKayboldu,
  s1PasifUyarisi,
} from '../lib/kuralAgirlik'
import { degisiklikleriBul, kirliMi, yazilacaklariBul } from '../lib/kuralDuzenleme'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
}

const SEKMELER = [
  'Talep',
  'Personel',
  'Yetkinlik',
  'Bina',
  'Görev Noktası',
  'Vardiya Tipi',
  'Kural',
] as const
type Sekme = (typeof SEKMELER)[number]

// Ekle/Değiştir/Sil üçlüsünün geçerli olduğu sekmeler. Talep ve Kural dışarıda
// kalır ve bu bilinçli bir ayrımdır: talep matrisinde eklenecek bağımsız bir
// kayıt yoktur (satırlar görev noktalarından türer, hücreler yerinde
// düzenlenir); kural kataloğunda ise H1–H8/S1–S8 kodda tanımlı sınıflarla
// eşleşir, eklenip silinemez, yalnızca pasifleştirilir (SDD 3.2.1).
const TANIM_SEKMELERI = ['Personel', 'Yetkinlik', 'Bina', 'Görev Noktası', 'Vardiya Tipi'] as const
type TanimSekmesi = (typeof TANIM_SEKMELERI)[number]

const GUN_VARDIYA_SUTUNLARI: { baslik: string; gunTipi: GunTipi; vardiyaAdi: string }[] = [
  { baslik: 'GÜNDÜZ', gunTipi: 'hafta_ici', vardiyaAdi: 'Gündüz' },
  { baslik: 'AKŞAM', gunTipi: 'hafta_ici', vardiyaAdi: 'Akşam' },
  { baslik: 'GECE', gunTipi: 'hafta_ici', vardiyaAdi: 'Gece' },
  { baslik: 'H.SONU GÜNDÜZ', gunTipi: 'hafta_sonu', vardiyaAdi: 'Gündüz' },
  { baslik: 'H.SONU AKŞAM', gunTipi: 'hafta_sonu', vardiyaAdi: 'Akşam' },
  { baslik: 'H.SONU GECE', gunTipi: 'hafta_sonu', vardiyaAdi: 'Gece' },
]

// --- Kural satırının sütun genişlikleri -------------------------------------
// Sabit genişlik zorunlu: alanlar içeriğine göre büyüdüğünde her kuralın
// etiketi farklı uzunlukta olduğu için parametre kutuları satırdan satıra
// kayıyordu (TASARIM_REFERANSI'ndaki "genişleyen bileşenlere sabit genişlik"
// uyarısının aynısı). 240px, en uzun etiketi ("Azami ardışık çalışma günü
// (gün)") tek satırda tutar.
const PARAMETRE_SUTUNU = 'w-[240px] shrink-0'
const AGIRLIK_SUTUNU = 'w-[92px] shrink-0'
// Rozet 64px, düzenleme kipindeki "☑ Aktif" ~62px; ikisi de aynı yuvada
// sağa yaslanır, böylece sütun kip değiştirince oynamaz.
const AKTIFLIK_SUTUNU = 'w-[92px] shrink-0'
// Etiket üstte, değer altta; ikisi de sağa yaslı.
const ALAN_YIGINI = 'flex flex-col items-end gap-1'
const DEGER_ALANI = 'w-24 text-right'

const INPUT_SINIFI =
  'h-8 w-full rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

export function TanimlarEkrani({ ekranSec }: Props) {
  const [sekme, setSekme] = useState<Sekme>('Talep')
  const [ekleAcik, setEkleAcik] = useState(false)

  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [yetkinlikler, setYetkinlikler] = useState<Yetkinlik[]>([])
  const [binalar, setBinalar] = useState<Bina[]>([])
  const [noktalar, setNoktalar] = useState<GorevNoktasi[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])
  const [talepHucreleri, setTalepHucreleri] = useState<TalepHucresi[]>([])
  const [yukGostergesi, setYukGostergesi] = useState<YukGostergesi | null>(null)
  const [kurallar, setKurallar] = useState<Kural[]>([])
  const [hata, setHata] = useState<string | null>(null)

  const [seciliId, setSeciliId] = useState<number | null>(null)
  const [duzenleniyor, setDuzenleniyor] = useState(false)
  const [silinecek, setSilinecek] = useState<{ yol: TanimYolu; id: number; ad: string } | null>(
    null,
  )
  const [pasifleriGoster, setPasifleriGoster] = useState(false)

  // Kural sekmesi düzenleme kipi (madde 3a). Kip kapalıyken hiçbir alan tek
  // tıkla değişmez; değişiklikler `kuralTaslagi` içinde birikir ve yalnızca
  // onaydan sonra sunucuya gider.
  const [kuralKipi, setKuralKipi] = useState<'okuma' | 'duzenleme'>('okuma')
  const [kuralTaslagi, setKuralTaslagi] = useState<Kural[]>([])
  // Onay şeridi. `hedefSekme` doluysa onay, sekmeden ayrılma isteğinden
  // doğmuştur ve kaydetme/atma sonrası o sekmeye geçilir.
  const [kuralOnayi, setKuralOnayi] = useState<{ hedefSekme: Sekme | null } | null>(null)
  const [kuralKaydediliyor, setKuralKaydediliyor] = useState(false)

  const hepsiniYukle = () => {
    Promise.all([
      api.personelListele(),
      api.yetkinlikListele(),
      api.binaListele(),
      api.noktaListele(),
      api.vardiyaTipiListele(),
      api.talepGetir(),
      api.kuralListele(),
    ])
      .then(([p, y, b, n, v, t, k]) => {
        setPersonelListesi(p)
        setYetkinlikler(y)
        setBinalar(b)
        setNoktalar(n)
        setVardiyaTipleri(v)
        setTalepHucreleri(t.hucreler)
        setYukGostergesi(t.yuk_gostergesi)
        setKurallar(k)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tanımlar yüklenemedi'))
  }

  useEffect(hepsiniYukle, [])

  const yetkinlikMap = useMemo(
    () => new Map(yetkinlikler.map((y) => [y.yetkinlik_id, y])),
    [yetkinlikler],
  )
  const vardiyaAdIdMap = useMemo(
    () => new Map(vardiyaTipleri.map((v) => [v.ad, v.vardiya_tipi_id])),
    [vardiyaTipleri],
  )

  const talepHucreBul = (noktaId: number, gunTipi: GunTipi, vardiyaTipiId: number | undefined) =>
    talepHucreleri.find(
      (h) => h.nokta_id === noktaId && h.gun_tipi === gunTipi && h.vardiya_tipi_id === vardiyaTipiId,
    )

  const talepGuncelle = async (
    noktaId: number,
    gunTipi: GunTipi,
    vardiyaTipiId: number,
    gerekenSayi: number,
  ) => {
    try {
      const yanit = await api.talepHucresiGuncelle({
        nokta_id: noktaId,
        vardiya_tipi_id: vardiyaTipiId,
        gun_tipi: gunTipi,
        tarih: null,
        gereken_sayi: gerekenSayi,
      })
      setTalepHucreleri(yanit.hucreler)
      setYukGostergesi(yanit.yuk_gostergesi)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Talep güncellenemedi')
    }
  }

  const kuralDuzenlemeAc = () => {
    setKuralTaslagi(kurallar.map((k) => ({ ...k, parametreler: { ...k.parametreler } })))
    setKuralKipi('duzenleme')
    setHata(null)
  }

  const kuralTaslaginiDegistir = (
    kimlik: string,
    veri: Partial<Pick<Kural, 'agirlik' | 'aktif' | 'parametreler'>>,
  ) => {
    setKuralTaslagi((mevcut) =>
      mevcut.map((k) =>
        k.kimlik === kimlik
          ? {
              ...k,
              ...veri,
              parametreler: veri.parametreler
                ? { ...k.parametreler, ...veri.parametreler }
                : k.parametreler,
            }
          : k,
      ),
    )
  }

  const kuralKirli = kirliMi(kurallar, kuralTaslagi)
  const kuralDegisiklikleri = degisiklikleriBul(kurallar, kuralTaslagi)

  const kuralKipiniKapat = (hedefSekme: Sekme | null) => {
    setKuralKipi('okuma')
    setKuralTaslagi([])
    setKuralOnayi(null)
    if (hedefSekme) setSekme(hedefSekme)
  }

  /** Kipten çıkış isteği: kirliyse onay ister, temizse doğrudan kapatır. */
  const kuralCikisIste = (hedefSekme: Sekme | null) => {
    if (kuralKirli) setKuralOnayi({ hedefSekme })
    else kuralKipiniKapat(hedefSekme)
  }

  const kuralKaydet = async (hedefSekme: Sekme | null) => {
    setKuralKaydediliyor(true)
    setHata(null)
    try {
      // Kural başına tek istek, yalnızca değişen alanlarla.
      for (const { kimlik, govde } of yazilacaklariBul(kurallar, kuralTaslagi)) {
        await api.kuralGuncelle(kimlik, govde)
      }
      setKurallar(await api.kuralListele())
      kuralKipiniKapat(hedefSekme)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Kural güncellenemedi')
    } finally {
      setKuralKaydediliyor(false)
    }
  }

  // Her sekmenin satırı NASIL görüneceğini tarif eder; düzeni ve eylem
  // çubuğunu TanimYonetimi kurar, böylece üçlü bütün sekmelerde aynı yerde
  // ve aynı görünümde kalır.
  const gorunumler: Record<TanimSekmesi, TanimGorunumu<unknown>> = {
    Personel: gorunumKur({
      yol: 'personel',
      kayitlar: personelListesi,
      kimlik: (p: Personel) => p.personel_id,
      baslik: (p: Personel) => p.ad_soyad,
      ozet: (p: Personel) => (
        <>
          {p.sicil_no} · <Sayi>{p.haftalik_hedef_saat}</Sayi> sa ·{' '}
          {p.yetkinlik_idleri.map((id) => yetkinlikMap.get(id)?.ad ?? id).join(', ') ||
            'yetkinlik yok'}
          {p.sabit_vardiya_tipi_id
            ? ` · sabit: ${vardiyaTipleri.find((v) => v.vardiya_tipi_id === p.sabit_vardiya_tipi_id)?.ad ?? '—'}`
            : ''}
        </>
      ),
      // Personelin `aktif` bayrağı yoktur; aktiflik tarih aralığıyla ifade
      // edilir (SDD 4.2.1) ve pasifleştirme aralığı dünde kapatır.
      aktifMi: (p: Personel) => !p.aktif_bitis || p.aktif_bitis >= bugunIso(),
    }),
    Yetkinlik: gorunumKur({
      yol: 'yetkinlik',
      kayitlar: yetkinlikler,
      kimlik: (y: Yetkinlik) => y.yetkinlik_id,
      baslik: (y: Yetkinlik) => y.ad,
      ozet: (y: Yetkinlik) => (
        <>
          {y.aciklama ? `${y.aciklama} · ` : ''}
          <Sayi>
            {personelListesi.filter((p) => p.yetkinlik_idleri.includes(y.yetkinlik_id)).length}
          </Sayi>{' '}
          personel
        </>
      ),
      aktifMi: (y: Yetkinlik) => y.aktif,
    }),
    Bina: gorunumKur({
      yol: 'bina',
      kayitlar: binalar,
      kimlik: (b: Bina) => b.bina_id,
      baslik: (b: Bina) => b.ad,
      ozet: (b: Bina) => `${noktalar.filter((n) => n.bina_id === b.bina_id).length} görev noktası`,
      aktifMi: (b: Bina) => b.aktif,
      bosMesaji:
        'Bina tanımlı değil — mevcut uygulama alanında bütün noktalar tesis geneli (SRS 3.3.3).',
    }),
    'Görev Noktası': gorunumKur({
      yol: 'nokta',
      kayitlar: noktalar,
      kimlik: (n: GorevNoktasi) => n.nokta_id,
      baslik: (n: GorevNoktasi) => n.ad,
      ozet: (n: GorevNoktasi) =>
        `${n.bina_id ? (binalar.find((b) => b.bina_id === n.bina_id)?.ad ?? 'Bina') : 'Tesis geneli'} · ${
          n.onkosul_yetkinlik_id
            ? (yetkinlikMap.get(n.onkosul_yetkinlik_id)?.ad ?? 'Ön koşul var')
            : 'Ön koşul yok'
        }`,
      aktifMi: (n: GorevNoktasi) => n.aktif,
    }),
    'Vardiya Tipi': gorunumKur({
      yol: 'vardiya-tipi',
      kayitlar: vardiyaTipleri,
      kimlik: (v: VardiyaTipi) => v.vardiya_tipi_id,
      baslik: (v: VardiyaTipi) => v.ad,
      ozet: (v: VardiyaTipi) => (
        <span className="font-mono">
          {v.baslangic_saati.slice(0, 5)} – {v.bitis_saati.slice(0, 5)} ·{' '}
          <Sayi>{v.sure_saat}</Sayi> saat
        </span>
      ),
      aktifMi: (v: VardiyaTipi) => v.aktif,
      ekRozet: (v: VardiyaTipi) =>
        v.gece_mi ? (
          <Rozet varyant="kilitli" genislik={64}>
            Gece
          </Rozet>
        ) : null,
    }),
  }

  const tanimSekmesiMi = (s: Sekme): s is TanimSekmesi =>
    (TANIM_SEKMELERI as readonly string[]).includes(s)
  const gorunum = tanimSekmesiMi(sekme) ? gorunumler[sekme] : null
  const seciliKayit =
    gorunum && seciliId !== null
      ? (gorunum.kayitlar.find((k) => gorunum.kimlik(k) === seciliId) ?? null)
      : null

  // Ekranda gösterilen liste: düzenleme kipinde taslak, okuma kipinde kayıtlı
  // hâl. Uyarılar da bundan hesaplanır, böylece kullanıcı KAYDEDECEĞİ durumun
  // sonucunu görür.
  const gosterilenKurallar = kuralKipi === 'duzenleme' ? kuralTaslagi : kurallar
  const zorunluKurallar = gosterilenKurallar.filter((k) => k.tip === 'zorunlu')
  const esnekKurallar = gosterilenKurallar.filter((k) => k.tip === 'esnek')

  // S1 uyarısının ölçüsü (madde 2d) — hesap lib/kuralAgirlik.ts'te, orada
  // testleri var.
  const s1Agirligi = esnekKurallar.find((k) => k.kimlik === 'S1')?.agirlik ?? null
  const esnekAgirlikToplami = digerEsnekAgirlikToplami(gosterilenKurallar)
  // Sütun sayısı KART BAŞINA hesaplanır: iki kart ayrı tablolar, hizalanması
  // gereken de kartın kendi içidir. Ortak bir sayı, parametresi hiç olmayan
  // esnek hedefler kartında boş bir sütun bırakırdı.
  const azamiParametre = (liste: Kural[]) =>
    liste.reduce((azami, k) => Math.max(azami, k.parametre_tanimlari.length), 0)
  const zorunluParametreSutunu = azamiParametre(zorunluKurallar)
  const esnekParametreSutunu = azamiParametre(esnekKurallar)
  const s1Uyarisi = s1PasifUyarisi(gosterilenKurallar)

  return (
    <AppShell
      aktifEkran="Tanımlar"
      ekranSec={ekranSec}
      baslik="Tanımlar"
      // Ekle/Değiştir/Sil üçlüsü üst çubuğun sağında; beş tanım sekmesinin
      // hepsinde aynı konum, aynı sıra, aynı görünüm. Önceki hâlinde "Ekle"
      // yan menünün altındaydı ve yalnız bazı sekmelerde vardı.
      aksiyonlar={
        sekme === 'Kural' ? (
          kuralKipi === 'okuma' ? (
            <Buton varyant="birincil" onClick={kuralDuzenlemeAc}>
              Değiştir
            </Buton>
          ) : (
            <>
              <Buton
                varyant="birincil"
                disabled={kuralKaydediliyor || !kuralKirli}
                title={kuralKirli ? undefined : 'Değişiklik yok'}
                onClick={() => setKuralOnayi({ hedefSekme: null })}
              >
                Kaydet
              </Buton>
              <Buton varyant="ikincil" onClick={() => kuralCikisIste(null)}>
                Vazgeç
              </Buton>
            </>
          )
        ) : (
          gorunum && (
          <>
            <Buton
              varyant="birincil"
              onClick={() => {
                setSeciliId(null)
                setDuzenleniyor(false)
                setEkleAcik(true)
              }}
            >
              Ekle
            </Buton>
            <Buton
              varyant="ikincil"
              disabled={seciliKayit === null}
              title={seciliKayit === null ? 'Önce listeden bir kayıt seçin' : undefined}
              onClick={() => {
                setDuzenleniyor(true)
                setEkleAcik(true)
              }}
            >
              Değiştir
            </Buton>
            <Buton
              varyant="ikincil"
              disabled={seciliKayit === null}
              title={seciliKayit === null ? 'Önce listeden bir kayıt seçin' : undefined}
              onClick={() => {
                if (!gorunum?.yol || seciliKayit === null || seciliId === null) return
                setEkleAcik(false)
                setSilinecek({
                  yol: gorunum.yol,
                  id: seciliId,
                  ad: gorunum.baslik(seciliKayit),
                })
              }}
            >
              Sil
            </Buton>
          </>
          )
        )
      }
    >
      {hata && <p className="text-sm text-signal">{hata}</p>}

      <div className="flex items-center justify-between gap-4 border-b border-rule pb-0">
        <div className="flex gap-0.5">
          {SEKMELER.map((s) => (
            <button
              key={s}
              type="button"
              className={cn(
                'rounded-t-sm px-4 py-2.5 text-sm text-ink-muted transition-colors',
                s === sekme && 'bg-chrome-base font-medium text-chrome-ink',
              )}
              onClick={() => {
                // Kaydedilmemiş kural değişikliğiyle sekmeden ayrılmak sessizce
                // veri kaybettirir; onay istenir ve geçiş ona bağlanır.
                if (sekme === 'Kural' && kuralKipi === 'duzenleme' && kuralKirli) {
                  setKuralOnayi({ hedefSekme: s })
                  return
                }
                if (sekme === 'Kural') kuralKipiniKapat(null)
                setSekme(s)
                setEkleAcik(false)
                setDuzenleniyor(false)
                setSeciliId(null)
                setSilinecek(null)
              }}
            >
              {s}
            </button>
          ))}
        </div>
        {gorunum && (
          <label className="flex shrink-0 items-center gap-2 pb-2 text-sm text-ink-muted">
            <input
              type="checkbox"
              checked={pasifleriGoster}
              onChange={(e) => setPasifleriGoster(e.target.checked)}
              className="accent-accent"
            />
            Pasifleri göster
          </label>
        )}
      </div>

      {ekleAcik && gorunum && (
        <EkleFormu
          sekme={sekme}
          binalar={binalar}
          yetkinlikler={yetkinlikler}
          duzenlenen={duzenleniyor ? seciliKayit : null}
          onIptal={() => {
            setEkleAcik(false)
            setDuzenleniyor(false)
          }}
          onKaydedildi={() => {
            setDuzenleniyor(false)
            setEkleAcik(false)
            hepsiniYukle()
          }}
          onHata={setHata}
        />
      )}

      {sekme === 'Talep' && (
        <>
          <Kart>
            <KartEtiketi>talep matrisi · görev noktası × gün tipi/vardiya</KartEtiketi>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] border-collapse">
                <thead>
                  <tr className="bg-sunken">
                    <th className="whitespace-nowrap px-3 py-2 text-left font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                      GÖREV NOKTASI
                    </th>
                    {GUN_VARDIYA_SUTUNLARI.map((sutun) => (
                      <th
                        key={sutun.baslik}
                        className="whitespace-nowrap px-3 py-2 text-left font-condensed text-[10px] tracking-[0.1em] text-ink-muted"
                      >
                        {sutun.baslik}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {noktalar.map((n) => (
                    <tr key={n.nokta_id} className="border-t border-rule">
                      <td className="px-3 py-3 text-sm font-medium text-ink">{n.ad}</td>
                      {GUN_VARDIYA_SUTUNLARI.map((sutun) => {
                        const vardiyaTipiId = vardiyaAdIdMap.get(sutun.vardiyaAdi)
                        const hucre = talepHucreBul(n.nokta_id, sutun.gunTipi, vardiyaTipiId)
                        return (
                          <td key={sutun.baslik} className="px-3 py-2">
                            <input
                              type="number"
                              min={0}
                              className={cn(INPUT_SINIFI, 'w-16 bg-sunken text-center')}
                              defaultValue={hucre?.gereken_sayi ?? 0}
                              onBlur={(e) => {
                                if (vardiyaTipiId === undefined) return
                                const deger = Number(e.target.value)
                                if (deger !== (hucre?.gereken_sayi ?? 0)) {
                                  talepGuncelle(n.nokta_id, sutun.gunTipi, vardiyaTipiId, deger)
                                }
                              }}
                            />
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Kart>
          {yukGostergesi && (
            <Kart className="bg-sunken">
              <div className="flex gap-10">
                <div>
                  <p className="m-0 font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                    HAFTALIK KİŞİ-VARDİYA YÜKÜ
                  </p>
                  <Sayi className="text-xl font-semibold text-ink">
                    {yukGostergesi.haftalik_kisi_vardiya}
                  </Sayi>
                </div>
                <div>
                  <p className="m-0 font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                    ASGARİ KADRO (KURAL PARAMETRELERİNE GÖRE)
                  </p>
                  <Sayi className="text-xl font-semibold text-ink">{yukGostergesi.asgari_kadro}</Sayi>
                </div>
                <div>
                  <p className="m-0 font-condensed text-[10px] tracking-[0.1em] text-ink-muted">
                    MEVCUT PERSONEL
                  </p>
                  <Sayi className="text-xl font-semibold text-ink">{personelListesi.length}</Sayi>
                </div>
              </div>
            </Kart>
          )}
        </>
      )}

      {TANIM_SEKMELERI.includes(sekme as TanimSekmesi) && (
        <>
          {silinecek && (
            <SilmeOnayi
              yol={silinecek.yol}
              id={silinecek.id}
              ad={silinecek.ad}
              onIptal={() => setSilinecek(null)}
              onSilindi={() => {
                setSilinecek(null)
                setSeciliId(null)
                hepsiniYukle()
              }}
            />
          )}
          <TanimListesi
            gorunum={gorunum!}
            seciliId={seciliId}
            seciliIdDegistir={setSeciliId}
            pasifleriGoster={pasifleriGoster}
          />
        </>
      )}

      {sekme === 'Kural' && (
        <>
          {kuralOnayi && (
            <Kart vurgulu>
              <KartEtiketi renk="accent">değişiklikleri kaydet</KartEtiketi>
              <p className="m-0 text-sm text-ink">
                {kuralDegisiklikleri.length} değişiklik kaydedilecek
                {kuralOnayi.hedefSekme
                  ? `, ardından ${kuralOnayi.hedefSekme} sekmesine geçilecek.`
                  : '.'}
              </p>
              <ul className="m-0 mt-2 flex list-none flex-col gap-1 p-0">
                {kuralDegisiklikleri.map((d, i) => (
                  <li key={i} className="text-sm text-ink-muted">
                    <span className="font-mono text-ink">{d.kimlik}</span> · {d.etiket}:{' '}
                    {d.onceki} → <span className="font-medium text-ink">{d.yeni}</span>
                  </li>
                ))}
              </ul>
              {/* S1 uyarıları onay anında da görünür: kullanıcı sonucunu
                  görerek onaylasın, kaydettikten sonra öğrenmesin. */}
              {s1Uyarisi && (
                <p className="mt-3 border-l-2 border-signal pl-3 text-sm text-signal">
                  {s1Uyarisi}
                </p>
              )}
              {s1BaskinligiKayboldu(s1Agirligi, esnekAgirlikToplami) && (
                <p className="mt-3 border-l-2 border-signal pl-3 text-sm text-signal">
                  S1 ağırlığı (<Sayi>{s1Agirligi}</Sayi>) diğer aktif esnek hedeflerin
                  toplamının (<Sayi>{esnekAgirlikToplami}</Sayi>) üzerinde değil; talep
                  karşılama baskınlığını kaybeder.
                </p>
              )}
              <div className="mt-4 flex gap-2">
                <Buton
                  varyant="birincil"
                  disabled={kuralKaydediliyor}
                  onClick={() => kuralKaydet(kuralOnayi.hedefSekme)}
                >
                  {kuralKaydediliyor ? 'Kaydediliyor…' : 'Kaydet'}
                </Buton>
                <Buton
                  varyant="ikincil"
                  disabled={kuralKaydediliyor}
                  onClick={() => kuralKipiniKapat(kuralOnayi.hedefSekme)}
                >
                  Kaydetme, at
                </Buton>
                <Buton
                  varyant="hayalet"
                  disabled={kuralKaydediliyor}
                  onClick={() => setKuralOnayi(null)}
                >
                  Düzenlemeye dön
                </Buton>
              </div>
            </Kart>
          )}
          <Kart>
            <KartEtiketi>H1–H8 · zorunlu kısıtlar</KartEtiketi>
            <p className="-mt-2 mb-4 text-sm text-ink-muted">
              Katalog kuralları modelin yapısını oluşturur; silinemez, yalnızca devre dışı
              bırakılır ve parametreleri değiştirilir.
            </p>
            <div className="flex flex-col">
              {zorunluKurallar.map((k) => (
                <KuralSatiri
                  key={k.kimlik}
                  kural={k}
                  s1Agirligi={s1Agirligi}
                  esnekAgirlikToplami={esnekAgirlikToplami}
                  duzenlenebilir={kuralKipi === 'duzenleme'}
                  parametreSutunu={zorunluParametreSutunu}
                  onGuncelle={kuralTaslaginiDegistir}
                />
              ))}
            </div>
          </Kart>
          <Kart>
            <KartEtiketi>S1–S8 · esnek hedefler</KartEtiketi>
            {s1Uyarisi && (
              <p className="-mt-2 mb-4 border-l-2 border-signal pl-3 text-sm text-signal">
                {s1Uyarisi}
              </p>
            )}
            <div className="flex flex-col">
              {esnekKurallar.map((k) => (
                <KuralSatiri
                  key={k.kimlik}
                  kural={k}
                  s1Agirligi={s1Agirligi}
                  esnekAgirlikToplami={esnekAgirlikToplami}
                  duzenlenebilir={kuralKipi === 'duzenleme'}
                  parametreSutunu={esnekParametreSutunu}
                  onGuncelle={kuralTaslaginiDegistir}
                />
              ))}
            </div>
          </Kart>
        </>
      )}
    </AppShell>
  )
}

interface KuralSatiriProps {
  kural: Kural
  s1Agirligi: number | null
  esnekAgirlikToplami: number
  /** Düzenleme kipi açık mı? Kapalıyken satırda hiçbir etkileşimli alan yoktur. */
  duzenlenebilir: boolean
  /**
   * Bu karttaki kuralların EN ÇOK kaç parametresi var.
   *
   * Satır kendi parametre sayısı kadar değil, bu sayı kadar sütun çizer;
   * eksik kalanlar boş bırakılır. Aksi hâlde parametresiz bir kuralın
   * (H1, H7, H8) ağırlık ve aktiflik alanları sola kayar ve sütunlar
   * satırdan satıra oynar.
   */
  parametreSutunu: number
  onGuncelle: (
    kimlik: string,
    veri: Partial<Pick<Kural, 'agirlik' | 'aktif' | 'parametreler'>>,
  ) => void
}

/**
 * Tek bir kuralın satırı (madde 2).
 *
 * Önceki hâlinde satırda yalnızca "H1" ve `JSON.stringify(parametreler)`
 * vardı. Artık katalogdaki okunabilir ad ve kısa açıklama gösteriliyor,
 * parametreler alan-değer olarak düzenleniyor.
 */
function KuralSatiri({
  kural,
  s1Agirligi,
  esnekAgirlikToplami,
  duzenlenebilir,
  parametreSutunu,
  onGuncelle,
}: KuralSatiriProps) {
  const esnek = kural.tip === 'esnek'
  const baskinlikUyarisi =
    kural.kimlik === 'S1' && s1BaskinligiKayboldu(s1Agirligi, esnekAgirlikToplami)

  return (
    <div className="border-t border-rule py-3 first:border-none">
      <div className="flex items-center gap-x-4">
        <span
          className={cn(
            'w-10 shrink-0 font-mono text-sm font-semibold',
            esnek ? 'text-accent' : 'text-ink',
          )}
        >
          {kural.kimlik}
        </span>
        <div className="min-w-[220px] flex-1">
          <p className="m-0 text-sm font-medium text-ink">{kural.ad}</p>
          <p className="m-0 mt-0.5 text-sm text-ink-muted">{kural.aciklama}</p>
        </div>

        {Array.from({ length: parametreSutunu }, (_, i) => {
          const tanim = kural.parametre_tanimlari[i]
          if (!tanim) return <div key={`bos-${i}`} className={PARAMETRE_SUTUNU} />
          return (
            <div key={tanim.anahtar} className={cn(PARAMETRE_SUTUNU, ALAN_YIGINI)}>
              <label
                htmlFor={`${kural.kimlik}-${tanim.anahtar}`}
                className="text-right text-sm text-ink-muted"
              >
                {tanim.etiket}
                {tanim.birim ? ` (${tanim.birim})` : ''}
              </label>
              {duzenlenebilir ? (
                <Input
                  id={`${kural.kimlik}-${tanim.anahtar}`}
                  type="number"
                  min={tanim.asgari ?? undefined}
                  max={tanim.azami ?? undefined}
                  className={cn(DEGER_ALANI, 'rounded-sm border-rule font-mono')}
                  // value + onChange (controlled): taslak tek doğruluk kaynağı.
                  // defaultValue ile bırakılırsa "kaydetme, at" sonrası alanda
                  // eski değer görünmeye devam ederdi.
                  value={String(kural.parametreler[tanim.anahtar] ?? '')}
                  onChange={(e) =>
                    onGuncelle(kural.kimlik, {
                      parametreler: { [tanim.anahtar]: Number(e.target.value) },
                    })
                  }
                />
              ) : (
                <Sayi className={cn(DEGER_ALANI, 'py-1 text-sm text-ink')}>
                  {String(kural.parametreler[tanim.anahtar] ?? '—')}
                </Sayi>
              )}
            </div>
          )
        })}

        {esnek && (
          <div className={cn(AGIRLIK_SUTUNU, ALAN_YIGINI)}>
            <label
              htmlFor={`${kural.kimlik}-agirlik`}
              className="text-right text-sm text-ink-muted"
            >
              Ağırlık
            </label>
            {duzenlenebilir ? (
              <Input
                id={`${kural.kimlik}-agirlik`}
                type="number"
                min={0}
                className={cn(DEGER_ALANI, 'rounded-sm border-rule font-mono')}
                value={String(kural.agirlik ?? '')}
                onChange={(e) => onGuncelle(kural.kimlik, { agirlik: Number(e.target.value) })}
              />
            ) : (
              <Sayi className={cn(DEGER_ALANI, 'py-1 text-sm text-ink')}>
                {kural.agirlik ?? '—'}
              </Sayi>
            )}
          </div>
        )}

        {/* Kip kapalıyken rozet salt gösterimdir. Tek tıkla değişen bir
            anahtar, yanlış bir tıkta kuralı sessizce ve geri dönüşsüz
            değiştiriyordu (canlıda S1 böyle pasifleşti). */}
        <div className={cn(AKTIFLIK_SUTUNU, 'flex justify-end')}>
          {duzenlenebilir ? (
            <label className="flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={kural.aktif}
                onChange={(e) => onGuncelle(kural.kimlik, { aktif: e.target.checked })}
                className="accent-accent"
              />
              Aktif
            </label>
          ) : (
            <Rozet varyant={kural.aktif ? 'dolu' : 'notr'} genislik={64}>
              {kural.aktif ? 'Aktif' : 'Pasif'}
            </Rozet>
          )}
        </div>
      </div>

      {baskinlikUyarisi && (
        <p className="mt-2 text-sm text-signal">
          S1 ağırlığı (<Sayi>{s1Agirligi}</Sayi>) diğer aktif esnek hedeflerin toplamının (
          <Sayi>{esnekAgirlikToplami}</Sayi>) üzerinde değil. Talep karşılama baskınlığını
          kaybeder: çözücü, adalet veya tercih gibi bir hedefi iyileştirmek için kapsama açığı
          bırakmayı tercih edebilir.
        </p>
      )}
    </div>
  )
}

interface EkleFormuProps {
  sekme: Sekme
  binalar: Bina[]
  yetkinlikler: Yetkinlik[]
  /** Dolu ise form düzenleme kipindedir; boş ise yeni kayıt açar. */
  duzenlenen: unknown | null
  onIptal: () => void
  onKaydedildi: () => void
  onHata: (mesaj: string) => void
}

/**
 * Ekleme ve değiştirme aynı formdan yürür (madde 1).
 *
 * İki ayrı form yazmak, alanların ve doğrulamaların iki yerde tanımlanması
 * demek olurdu; bu projede aynı kalıp daha önce birkaç kez soruna yol açtı.
 * Kip yalnızca başlangıç değerlerini ve POST/PUT seçimini değiştirir.
 */
function EkleFormu({
  sekme,
  binalar,
  yetkinlikler,
  duzenlenen,
  onIptal,
  onKaydedildi,
  onHata,
}: EkleFormuProps) {
  const mevcut = duzenlenen as Record<string, unknown> | null
  const kimlikAlani: Partial<Record<Sekme, string>> = {
    Personel: 'personel_id',
    Yetkinlik: 'yetkinlik_id',
    Bina: 'bina_id',
    'Görev Noktası': 'nokta_id',
    'Vardiya Tipi': 'vardiya_tipi_id',
  }
  const id = mevcut ? Number(mevcut[kimlikAlani[sekme] ?? '']) : null

  const ilkDeger = (anahtar: string, varsayilan = '') =>
    mevcut && mevcut[anahtar] != null ? String(mevcut[anahtar]) : varsayilan

  const [ad, setAd] = useState(() =>
    ilkDeger(sekme === 'Personel' ? 'ad_soyad' : 'ad'),
  )
  const [ikinciAlan, setIkinciAlan] = useState(() =>
    sekme === 'Personel'
      ? ilkDeger('sicil_no')
      : sekme === 'Yetkinlik'
        ? ilkDeger('aciklama')
        : sekme === 'Vardiya Tipi'
          ? ilkDeger('baslangic_saati').slice(0, 5)
          : '',
  )
  const [ucuncuAlan, setUcuncuAlan] = useState(() =>
    sekme === 'Personel'
      ? ilkDeger('haftalik_hedef_saat')
      : sekme === 'Vardiya Tipi'
        ? ilkDeger('bitis_saati').slice(0, 5)
        : '',
  )
  const [binaId, setBinaId] = useState(() => ilkDeger('bina_id'))
  const [yetkinlikId, setYetkinlikId] = useState(() =>
    sekme === 'Görev Noktası'
      ? ilkDeger('onkosul_yetkinlik_id')
      : sekme === 'Personel' && Array.isArray(mevcut?.yetkinlik_idleri)
        ? String((mevcut.yetkinlik_idleri as number[])[0] ?? '')
        : '',
  )
  const [gonderiliyor, setGonderiliyor] = useState(false)

  // Aktiflik, DÜZENLEME kipinde görünür bir alandır (madde 3b). Pasifleştirmenin
  // tek yolu Sil'di ve geri dönüşün yolu yoktu — kapı tek yönlüydü.
  //
  // Personel istisnadır: aktiflik orada bayrakla değil tarih aralığıyla ifade
  // edilir (SDD 4.2.1). Oradaki geri alma `aktif_bitis` alanını TEMİZLEMEKTİR;
  // bir bayrak eklemek aynı bilgiyi iki kaynağa ayırırdı.
  const personelMi = sekme === 'Personel'
  const [aktif, setAktif] = useState(() =>
    mevcut === null
      ? true
      : personelMi
        ? mevcut.aktif_bitis == null || String(mevcut.aktif_bitis) >= bugunIso()
        : mevcut.aktif !== false,
  )

  const kaydet = async () => {
    setGonderiliyor(true)
    try {
      if (sekme === 'Personel') {
        const govde = {
          ad_soyad: ad,
          sicil_no: ikinciAlan,
          haftalik_hedef_saat: Number(ucuncuAlan) || 40,
          yetkinlik_idleri: yetkinlikId ? [Number(yetkinlikId)] : [],
        }
        if (id !== null) {
          // Aktifleştirme = aktiflik penceresini yeniden açmak. Pasifleştirme
          // (aktif_bitis'i düne yazmak) sunucudaki DELETE yoluna aittir;
          // buradan yalnızca geri alınır.
          await api.personelGuncelle(id, aktif ? { ...govde, aktif_bitis: null } : govde)
        } else {
          await api.personelOlustur({ ...govde, aktif_baslangic: bugunIso() })
        }
      } else if (sekme === 'Yetkinlik') {
        if (id !== null)
          await api.yetkinlikGuncelle(id, { ad, aciklama: ikinciAlan || null, aktif })
        else await api.yetkinlikOlustur(ad, ikinciAlan || undefined)
      } else if (sekme === 'Bina') {
        if (id !== null) await api.binaGuncelle(id, { ad, aktif })
        else await api.binaOlustur(ad)
      } else if (sekme === 'Görev Noktası') {
        const binaDegeri = binaId ? Number(binaId) : null
        const yetkinlikDegeri = yetkinlikId ? Number(yetkinlikId) : null
        if (id !== null)
          await api.noktaGuncelle(id, {
            ad,
            bina_id: binaDegeri,
            onkosul_yetkinlik_id: yetkinlikDegeri,
            aktif,
          })
        else await api.noktaOlustur(ad, binaDegeri, yetkinlikDegeri)
      } else if (sekme === 'Vardiya Tipi') {
        if (id !== null)
          await api.vardiyaTipiGuncelle(id, {
            ad,
            baslangic_saati: ikinciAlan,
            bitis_saati: ucuncuAlan,
            aktif,
          })
        else await api.vardiyaTipiOlustur(ad, ikinciAlan, ucuncuAlan)
      }
      onKaydedildi()
    } catch (e) {
      onHata(e instanceof Error ? e.message : 'Kayıt kaydedilemedi')
    } finally {
      setGonderiliyor(false)
    }
  }

  return (
    <Kart vurgulu>
      <KartEtiketi renk="accent">
        {sekme.toLocaleLowerCase('tr-TR')} {id !== null ? 'değiştir' : 'ekle'}
      </KartEtiketi>
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm text-ink-muted">Ad</label>
          <Input value={ad} onChange={(e) => setAd(e.target.value)} className="w-52 rounded-sm border-rule" />
        </div>
        {sekme === 'Personel' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Sicil No</label>
              <Input
                value={ikinciAlan}
                onChange={(e) => setIkinciAlan(e.target.value)}
                className="w-32 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Hedef Saat</label>
              <Input
                type="number"
                value={ucuncuAlan}
                onChange={(e) => setUcuncuAlan(e.target.value)}
                placeholder="40"
                className="w-24 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Yetkinlik</label>
              <select
                className={INPUT_SINIFI}
                value={yetkinlikId}
                onChange={(e) => setYetkinlikId(e.target.value)}
              >
                <option value="">—</option>
                {yetkinlikler.map((y) => (
                  <option key={y.yetkinlik_id} value={y.yetkinlik_id}>
                    {y.ad}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
        {sekme === 'Yetkinlik' && (
          <div className="flex flex-col gap-1">
            <label className="text-sm text-ink-muted">Açıklama</label>
            <Input
              value={ikinciAlan}
              onChange={(e) => setIkinciAlan(e.target.value)}
              className="w-64 rounded-sm border-rule"
            />
          </div>
        )}
        {sekme === 'Görev Noktası' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Bina</label>
              <select className={INPUT_SINIFI} value={binaId} onChange={(e) => setBinaId(e.target.value)}>
                <option value="">Tesis geneli</option>
                {binalar.map((b) => (
                  <option key={b.bina_id} value={b.bina_id}>
                    {b.ad}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Ön Koşul Yetkinlik</label>
              <select
                className={INPUT_SINIFI}
                value={yetkinlikId}
                onChange={(e) => setYetkinlikId(e.target.value)}
              >
                <option value="">—</option>
                {yetkinlikler.map((y) => (
                  <option key={y.yetkinlik_id} value={y.yetkinlik_id}>
                    {y.ad}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
        {sekme === 'Vardiya Tipi' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Başlangıç</label>
              <Input
                type="time"
                value={ikinciAlan}
                onChange={(e) => setIkinciAlan(e.target.value)}
                className="w-28 rounded-sm border-rule font-mono"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Bitiş</label>
              <Input
                type="time"
                value={ucuncuAlan}
                onChange={(e) => setUcuncuAlan(e.target.value)}
                className="w-28 rounded-sm border-rule font-mono"
              />
            </div>
          </>
        )}
        {/* Aktiflik yalnızca DÜZENLEMEDE görünür: yeni kayıt zaten aktif
            doğar, kutuyu ekleme formunda göstermek anlamsız bir seçim sunardı. */}
        {id !== null && (
          <label className="flex items-center gap-2 self-end pb-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={aktif}
              onChange={(e) => setAktif(e.target.checked)}
              className="accent-accent"
            />
            Aktif
          </label>
        )}
        <Buton varyant="birincil" onClick={kaydet} disabled={gonderiliyor || !ad}>
          Kaydet
        </Buton>
        <Buton varyant="hayalet" onClick={onIptal}>
          İptal
        </Buton>
      </div>
      {id !== null && !aktif && (
        <p className="mt-3 text-sm text-ink-muted">
          Pasif kayıt yeni çözümlerde kullanılmaz; mevcut çizelgelerde görünmeye devam eder.
          {personelMi && ' Personelde bu, aktiflik penceresinin kapalı olması demektir.'}
        </p>
      )}
    </Kart>
  )
}
