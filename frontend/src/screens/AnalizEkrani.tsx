import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type {
  Analiz,
  AnalizCezaKalemi,
  CizelgeSurumu,
  Donem,
  KotaDurumu,
  KumulatifDegisim,
  Personel,
  Ufuk,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart, KartEtiketi, Sayi } from '../components/app-ui'
import { donemAraligiBicimle } from '../lib/tarih'
import { csvDisaAktar } from '../lib/disaAktarma'
import { cn } from '../lib/utils'
import { sayiBicimle, sapmaBicimle } from '../lib/sayi'
import { adaletSatirlari, type AdaletSatiri } from '../lib/adalet'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
}

const SECIM_SINIFI =
  'h-8 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30 disabled:opacity-50'

const SURUM_DURUM_METNI: Record<string, string> = {
  taslak: 'Taslak',
  cozuldu: 'Çözüldü',
  yayinlandi: 'Yayınlandı',
  arsiv: 'Arşiv',
}

function yuzdeBicimle(oran: number | null): string {
  return oran === null ? '—' : `%${Math.round(oran * 100)}`
}

// Birim burada eklenir, sayının kendisi lib/sayi.ts'ten gelir — işaret ve
// ondalık ayracı kararı tek yerde durur.
function saatSapmasi(sapma: number): string {
  return `${sapmaBicimle(sapma, 1)} sa`
}

export function AnalizEkrani({ ekranSec, donemId, donemIdSec }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [surumId, setSurumId] = useState<number | null>(null)
  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [analiz, setAnaliz] = useState<Analiz | null>(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [excelIniyor, setExcelIniyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)
  // UFUK ANAHTARI (SDD 6.3.4). Varsayılan dönem içi: kabul kriteri onu ölçer
  // (Charter 1.5) ve ekran ilk açıldığında o sayıyı göstermelidir.
  const [ufuk, setUfuk] = useState<Ufuk>('donem')

  useEffect(() => {
    Promise.all([api.donemler(), api.personelListele()])
      .then(([d, p]) => {
        setDonemler(d)
        setPersonelListesi(p)
        if (donemId === null && d[0]) donemIdSec(d[0].donem_id)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Tanımlar yüklenemedi'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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

  useEffect(() => {
    if (surumId === null) {
      setAnaliz(null)
      return
    }
    setYukleniyor(true)
    setHata(null)
    api
      .analizGetir(surumId, ufuk)
      .then(setAnaliz)
      .catch((e) => setHata(e instanceof Error ? e.message : 'Analiz yüklenemedi'))
      .finally(() => setYukleniyor(false))
  }, [surumId, ufuk])

  const donem = donemler.find((d) => d.donem_id === donemId) ?? null
  const surum = surumler.find((s) => s.surum_id === surumId) ?? null

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )

  /**
   * Adalet grafiğinin satırları — gece ve hafta sonu AYRI ölçülerdir.
   *
   * İki ölçü bir arada tek çubuğa yığılıyordu; artık her birinin kendi
   * referansı var (kişiye düşen adil pay) ve iki farklı hedefe göre sapmayı
   * tek çubuk üzerinde göstermek mümkün değil. Havuzlar da aynı değil:
   * yalnızca hafta içi talebi bulunan bir noktada çalışan personel hafta sonu
   * ölçüsünün dışındadır (SRS S3), gece ölçüsüne girebilir.
   */
  const geceSatirlari = useMemo(
    () => adaletSatirlari(analiz?.kisi_basina_gece ?? []),
    [analiz],
  )
  const haftaSonuSatirlari = useMemo(
    () => adaletSatirlari(analiz?.kisi_basina_hafta_sonu ?? []),
    [analiz],
  )

  const saatSapmasiOlanlar = (analiz?.saat_dagilimi ?? []).filter(
    (s) => Math.abs(s.sapma) > 1e-9,
  )

  // Ortanca sapma ve "hepsi aynı yönde mi": tablo renklendirmesi buna dayanır.
  const { ortancaSapma, hepsiAyniYonde, saatDilimi, saatGizlenen } = useMemo(() => {
    const sirali = [...saatSapmasiOlanlar].sort((a, b) => Math.abs(b.sapma) - Math.abs(a.sapma))
    const sapmalar = sirali.map((s) => s.sapma).sort((a, b) => a - b)
    const ortanca = sapmalar.length > 0 ? sapmalar[Math.floor(sapmalar.length / 2)]! : 0
    const dilim = sirali.slice(0, 12)
    return {
      ortancaSapma: ortanca,
      // HEPSİ AYNI YÖNDE: tümü artı ya da tümü eksi. Karma durumda dengesizlik
      // kişiler arasındadır ve not gösterilmez.
      hepsiAyniYonde:
        sapmalar.length > 1 &&
        (sapmalar.every((d) => d > 0) || sapmalar.every((d) => d < 0)),
      saatDilimi: dilim,
      saatGizlenen: sirali.length - dilim.length,
    }
  }, [saatSapmasiOlanlar])

  const cezaGirdileri = analiz?.ceza_dokumu
    ? Object.entries(analiz.ceza_dokumu).sort(([a], [b]) => a.localeCompare(b))
    : []
  const azamiCeza = cezaGirdileri.reduce((m, [, deger]) => Math.max(m, deger), 0)

  // Dışa aktarma Çizelge ekranıyla ortak (lib/disaAktarma.ts). Analiz ekranı
  // atamaları ve kapsama açığını kendi durumunda tutmadığından istek anında
  // çeker; biçimleme ve indirme yolunun kendisi paylaşılır.
  const disaAktar = async () => {
    if (surumId === null || !donem || !surum) return
    try {
      const [atamalar, kapsamaAcigi, fazlaKadro, noktalar] = await Promise.all([
        api.surumAtamalari(surumId),
        api.surumKapsamaAcigi(surumId),
        api.surumFazlaKadro(surumId),
        api.noktaListele(),
      ])
      csvDisaAktar({
        donem,
        surum,
        atamalar,
        kapsamaAcigi,
        fazlaKadro,
        personelMap,
        noktaMap: new Map(noktalar.map((n) => [n.nokta_id, n])),
      })
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Dışa aktarma başarısız')
    }
  }

  return (
    <AppShell
      aktifEkran="Analiz"
      donemId={donemId}
      ekranSec={ekranSec}
      baslik="Analiz"
      aksiyonlar={
        <>
          {/* Analizin Excel'i CIZELGENINKINDEN AYRI bir dosyadir: adalet
              dagilimi, kapsama acigi ve ceza dokumu cizelgenin yaninda degil
              kendi kitabinda durur (SRS FR-8.9). */}
          <Buton
            varyant="ikincil"
            onClick={() => {
              if (!surum) return
              setExcelIniyor(true)
              api
                .analizExcelIndir(surum.surum_id, surum.surum_no)
                .catch(() => setHata('Excel dosyası indirilemedi.'))
                .finally(() => setExcelIniyor(false))
            }}
            disabled={surum === null || excelIniyor}
          >
            {excelIniyor ? 'İndiriliyor…' : 'Excel'}
          </Buton>
          <Buton varyant="ikincil" onClick={disaAktar} disabled={surumId === null}>
            CSV
          </Buton>
        </>
      }
    >
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
      {yukleniyor && <p className="text-sm text-ink-muted">Yükleniyor…</p>}

      {analiz && (
        <>
          <div className="grid grid-cols-5 gap-4">
            <Kart>
              <KartEtiketi>dönem kapsaması</KartEtiketi>
              <p className="m-0 font-mono text-sayi-buyuk font-semibold text-accent">
                {yuzdeBicimle(analiz.kapsama_orani)}
              </p>
            </Kart>
            {/* Kapsama oranının YANINDA ama ondan ayrı: oran "talebin ne
                kadarı karşılandı" sorusunu yanıtlar; fazla kadro o soruya
                bir şey eklemez, fazla atama bir hücreyi daha iyi kapsamış
                olmaz (SRS 4.3 S1). */}
            <Kart>
              <KartEtiketi renk={analiz.toplam_fazla_kadro > 0 ? 'warn' : undefined}>
                talepten fazla
              </KartEtiketi>
              <p
                className={cn(
                  'm-0 font-mono text-sayi-buyuk font-semibold',
                  analiz.toplam_fazla_kadro > 0 ? 'text-signal' : 'text-ink',
                )}
              >
                {analiz.toplam_fazla_kadro}
              </p>
            </Kart>
            {/* KİŞİ-SAAT ile ARALIK SAYISI ayrı ölçüler (SDD 6.3.4): ardışık
                saatler tek kayıtta birleştiği için satır sayısı yükü
                anlatmaz. İkisi karıştırıldı ve dışa aktarma başlığında yanlış
                sayı gösterildi; bu yüzden ikisi de, yan yana. */}
            <Kart>
              <KartEtiketi renk={analiz.karsilanmayan_kisi_saat > 0 ? 'warn' : undefined}>
                karşılanmayan
              </KartEtiketi>
              <p
                className={cn(
                  'm-0 font-mono text-sayi-buyuk font-semibold',
                  analiz.karsilanmayan_kisi_saat > 0 ? 'text-signal' : 'text-ink',
                )}
              >
                {sayiBicimle(analiz.karsilanmayan_kisi_saat, 0)}
                <span className="ml-1 font-sans text-sm font-normal text-ink-muted">kişi-saat</span>
              </p>
              <p className="m-0 text-sm text-ink-muted">
                {analiz.acik_aralik_sayisi} açık aralık
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>tercih karşılama</KartEtiketi>
              <p className="m-0 font-mono text-sayi-buyuk font-semibold text-ink">
                {yuzdeBicimle(analiz.tercih_karsilama_orani)}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>en dengesiz</KartEtiketi>
              <p className="m-0 text-sayi-buyuk font-semibold text-signal">
                {analiz.en_dengesiz_ad_soyad ?? '—'}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>toplam ceza</KartEtiketi>
              <Sayi className="text-sayi-buyuk font-semibold text-ink">
                {analiz.toplam_ceza !== null ? sayiBicimle(analiz.toplam_ceza, 0) : '—'}
              </Sayi>
            </Kart>
          </div>

          {/* UFUK ANAHTARI adalet kartlarının ÜSTÜNDE ve hangi ufkun seçili
              olduğu her zaman görünür: iki ufkun sayıları farklıdır ve
              belirsiz kalırsa tablo yanlış okunur (SDD 6.3.4). */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="mono-caps text-ink-muted">ölçüm ufku</span>
            <div className="flex gap-1" role="group" aria-label="Ölçüm ufku">
              {(
                [
                  ['donem', 'Planlama dönemi'],
                  ['adalet', 'Adalet ufku · 90 gün'],
                ] as const
              ).map(([deger, etiket]) => (
                <button
                  key={deger}
                  type="button"
                  aria-pressed={ufuk === deger}
                  onClick={() => setUfuk(deger)}
                  className={cn(
                    'h-8 rounded-sm border px-3 font-mono text-sm',
                    ufuk === deger
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-rule bg-surface text-ink-muted',
                  )}
                >
                  {etiket}
                </button>
              ))}
            </div>
            <span className="text-sm text-ink-muted">
              {ufuk === 'donem'
                ? 'Yük ve pay yalnızca bu dönemi kapsar (kabul kriteri, Charter 5).'
                : 'Yük ve pay son doksan günü kapsar; geçmiş yayınlanmış sürümler dahil (SRS TD-6).'}
            </span>
          </div>

          <AdaletGrafigi
            etiket="gece saati dağılımı · kişi başına"
            satirlar={geceSatirlari}
            cubukSinifi="bg-vardiya-gece"
            bosMetin="Bu sürümde gece ataması yok."
            havuzAciklamasi="Ölçü, gece talebine erişebilen personeli kapsar (SRS S2, P_gece)."
          />

          <AdaletGrafigi
            etiket="hafta sonu saati dağılımı · kişi başına"
            satirlar={haftaSonuSatirlari}
            cubukSinifi="bg-accent"
            bosMetin="Bu sürümde hafta sonu ataması yok."
            havuzAciklamasi="Ölçü, hafta sonu talebine erişebilen personeli kapsar (SRS S3, P_hs)."
          />

          <Kart>
            <KartEtiketi>toplam saat dengesi · personel başına</KartEtiketi>
            {saatSapmasiOlanlar.length === 0 ? (
              <p className="text-sm text-ink-muted">Herkes kendi adil payını tutturdu.</p>
            ) : (
              <table className="w-full min-w-[560px] border-collapse">
                <thead>
                  <tr className="bg-sunken">
                    {/* Taban "HEDEF" değil ADİL PAYDIR (SRS S4): kişisel
                        sözleşme saati ulaşılabilir bir hedef olmadığından
                        herkes aynı yönde sapmalı görünüyor ve tablo hiçbir
                        ayrım üretmiyordu. Sütun adı da bunu söylemeli. */}
                    {['PERSONEL', 'TOPLAM SAAT', 'ADİL PAY', 'SAPMA'].map((b) => (
                      <th
                        key={b}
                        className="mono-caps whitespace-nowrap px-3 py-2 text-left text-ink-muted"
                      >
                        {b}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {saatDilimi.map((s) => (
                    <tr key={s.personel_id} className="border-t border-rule">
                      <td className="px-3 py-3 text-sm font-medium text-ink">{s.ad_soyad}</td>
                      <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                        {sayiBicimle(s.toplam_saat, 0)} sa
                      </td>
                      <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                        {sayiBicimle(s.hedef_saat, 0)} sa
                      </td>
                      {/* RENK, ORTANCADAN UZAKLIĞA GÖRE. Mutlak büyüklüğe
                          bakılıyordu ve talep hedeflerin toplamından düşük
                          olduğunda HERKES kırmızı çıkıyordu — tablo hiçbir
                          ayrım üretmiyordu. Kişiler arası fark anlamlıdır,
                          herkesin ortak kayması senaryonun özelliğidir. */}
                      <td
                        className={cn(
                          'px-3 py-3 font-mono text-sm font-semibold',
                          Math.abs(s.sapma - ortancaSapma) > 15 ? 'text-signal' : 'text-ink',
                        )}
                      >
                        {saatSapmasi(s.sapma)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {saatSapmasiOlanlar.length > 0 && (
              <p className="mt-3 text-xs text-ink-muted">
                {hepsiAyniYonde
                  ? `Bu dönemde herkesin toplamı payının ${ortancaSapma < 0 ? 'altında' : 'üstünde'}: talep, hedeflerin toplamıyla örtüşmüyor. Anlamlı olan kişiler arası fark — renk ortancadan (${saatSapmasi(ortancaSapma)}) uzaklığa göre.`
                  : 'Renk, ortancadan on beş saatten fazla uzaklaşan kişileri işaretler.'}
                {saatGizlenen > 0 && ` En uzaktaki ${saatDilimi.length} kişi gösteriliyor.`}
              </p>
            )}
          </Kart>

          {cezaGirdileri.length > 0 && (
            <Kart>
              <KartEtiketi>ceza dökümü</KartEtiketi>
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {cezaGirdileri.map(([kimlik, deger]) => (
                  <li key={kimlik} className="flex items-center gap-3 py-1 text-sm">
                    <span className="w-28 shrink-0 text-ink-muted">{kimlik}</span>
                    <span className="h-2 flex-1 overflow-hidden rounded-sm bg-sunken">
                      <span
                        className={kimlik === 'S1' ? 'block h-full bg-signal' : 'block h-full bg-accent'}
                        style={{
                          width: azamiCeza > 0 ? `${Math.max(2, (deger / azamiCeza) * 100)}%` : '0%',
                        }}
                      />
                    </span>
                    <Sayi className="w-16 shrink-0 text-right text-ink">{deger}</Sayi>
                  </li>
                ))}
              </ul>
            </Kart>
          )}

          {analiz.bina_degisim_sayisi.length > 0 && (
            <Kart>
              <KartEtiketi renk="warn">bina değişim sayısı</KartEtiketi>
              <ul className="m-0 flex list-none flex-col p-0">
                {analiz.bina_degisim_sayisi.map((b) => (
                  <li
                    key={b.personel_id}
                    className="flex items-center justify-between border-t border-rule py-2 text-sm first:border-none"
                  >
                    <span className="text-ink">{b.ad_soyad}</span>
                    <Sayi className="text-ink-muted">{b.sayi}</Sayi>
                  </li>
                ))}
              </ul>
            </Kart>
          )}

          <KotaKarti satirlar={analiz.kota_durumu} />
          <CezaDokumu kalemler={analiz.ceza_kalemleri} toplam={analiz.toplam_ceza} />
          <KumulatifDegisimKarti degisim={analiz.kumulatif_degisim} />
        </>
      )}
    </AppShell>
  )
}

/**
 * Adalet grafiği — referans çizgisi KİŞİYE DÜŞEN ADİL PAY (SRS S2/S3).
 *
 * Önceki hâlinde referans havuz ortalamasıydı. S2'nin metni o ölçüyü açıkça
 * reddediyor: erişilebilirliği kısıtlı bir havuz — yalnızca tek bir noktada
 * çalışabilen personel gibi — ortalamaya hiçbir çizelgeyle ulaşamaz ve kalıcı
 * olarak sapmalı görünür. Bu bir adaletsizlik değil yapısal bir sınırdır;
 * ölçünün onu sapma olarak raporlaması, ölçüyü ayırt edici olmaktan çıkarır.
 * Herkesin aynı yönde saptığını gösteren bir grafik hiçbir şey göstermez.
 *
 * Pay kişiden kişiye değiştiği için referans TEK BİR ÇİZGİ DEĞİL, satır başına
 * bir işarettir; ölçek satırlar arasında ortaktır, yoksa çubuk uzunlukları
 * karşılaştırılamaz.
 */
function AdaletGrafigi({
  etiket,
  satirlar,
  cubukSinifi,
  bosMetin,
  havuzAciklamasi,
}: {
  etiket: string
  satirlar: readonly AdaletSatiri[]
  cubukSinifi: string
  bosMetin: string
  havuzAciklamasi: string
}) {
  const azami = satirlar.reduce((m, s) => Math.max(m, s.saat, s.pay), 0)
  const oran = (deger: number) => (azami > 0 ? `${(deger / azami) * 100}%` : '0%')

  // KART LİSTE DEĞİL, SAPMA GÖSTERİR. Otuz kişilik bir havuzda otuz çubuk
  // basıldığında en uzaktakiler görsel olarak kayboluyordu; satırlar zaten
  // sapmaya göre sıralı, ilk sekizi soruyu yanıtlıyor. Kalanı isteyen açar.
  const ILK_GOSTERILEN = 8
  const [hepsi, setHepsi] = useState(false)
  const gosterilen = hepsi ? satirlar : satirlar.slice(0, ILK_GOSTERILEN)
  const gizlenen = satirlar.length - gosterilen.length

  return (
    <Kart>
      <KartEtiketi>{etiket}</KartEtiketi>
      {satirlar.length === 0 ? (
        <p className="text-sm text-ink-muted">{bosMetin}</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {gosterilen.map((s) => (
            <li key={s.personel_id} className="flex items-center gap-3 text-sm">
              <span className="w-52 shrink-0 truncate text-ink" title={s.ad_soyad}>
                {s.ad_soyad}
              </span>
              <span className="relative flex h-2.5 flex-1 overflow-hidden rounded-sm bg-sunken">
                <span className={cn('block h-full', cubukSinifi)} style={{ width: oran(s.saat) }} />
                {/* Referans çizgisi: bu KİŞİNİN payı. */}
                <span
                  className="absolute inset-y-[-3px] w-px bg-ink"
                  style={{ left: oran(s.pay) }}
                  aria-hidden="true"
                />
              </span>
              <Sayi className="w-14 shrink-0 text-right text-ink">
                {sayiBicimle(s.saat, 0)} sa
              </Sayi>
              <Sayi className="w-20 shrink-0 text-right text-ink-muted">
                pay {sayiBicimle(s.pay, 1)}
              </Sayi>
              {/* Sayı İŞARETSİZDİR (çözücünün formülü öyle); yönü çubuğun
                  referansa göre konumu söyler. */}
              <span
                className="w-16 shrink-0 text-right"
                title={
                  s.sapma > 0
                    ? `Çözücünün cezalandırdığı sapma: ${sayiBicimle(s.sapma, 0)} saat`
                    : 'Adil payın taban/tavan bandı içinde — cezasız'
                }
              >
                <Sayi
                  className={cn('font-semibold', s.sapma > 0 ? 'text-signal' : 'text-ink-muted')}
                >
                  {s.sapma > 0 ? `${sayiBicimle(s.sapma, 0)} sa` : '—'}
                </Sayi>
              </span>
            </li>
          ))}
        </ul>
      )}
      {gizlenen > 0 && (
        <button
          type="button"
          onClick={() => setHepsi(true)}
          className="mt-3 font-mono text-sm text-accent underline-offset-2 hover:underline"
        >
          {gizlenen} kişi daha göster
        </button>
      )}
      {hepsi && satirlar.length > ILK_GOSTERILEN && (
        <button
          type="button"
          onClick={() => setHepsi(false)}
          className="mt-3 font-mono text-sm text-ink-muted underline-offset-2 hover:underline"
        >
          Yalnız en uzaktaki {ILK_GOSTERILEN} kişi
        </button>
      )}
      <p className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-px bg-ink" /> kişiye düşen adil pay (referans)
        </span>
        <span>{havuzAciklamasi}</span>
      </p>
    </Kart>
  )
}


/** H10: kimin kotası doluyor (SDD 6.3.4).

    Sunucu SIRALI gönderir — sınıra dayanan üstte. Sıralamayı burada yapmak,
    aynı kararın iki yerde durması olurdu; üstelik dışa aktarma da aynı
    sırayı kullanıyor.

    Kartın amacı listeyi göstermek değil RİSKİ göstermek: otuz kişilik bir
    tabloda kimin sınıra yaklaştığı, tam liste basıldığında kaybolur. */
function KotaKarti({ satirlar }: { satirlar: KotaDurumu[] }) {
  const RISK_ESIGI = 40
  const riskliler = satirlar.filter((k) => k.kalan_kota_saat <= RISK_ESIGI)
  const gosterilen = riskliler.length > 0 ? riskliler : satirlar.slice(0, 5)

  return (
    <Kart>
      <KartEtiketi renk={riskliler.length > 0 ? 'warn' : undefined}>
        yıllık fazla çalışma kotası
      </KartEtiketi>
      {satirlar.length === 0 ? (
        <p className="text-sm text-ink-muted">Kota bilgisi yok.</p>
      ) : (
        <>
          <table className="w-full min-w-[420px] border-collapse">
            <thead>
              <tr className="bg-sunken">
                {['PERSONEL', 'FAZLA ÇALIŞMA', 'KALAN KOTA'].map((b) => (
                  <th
                    key={b}
                    className="mono-caps whitespace-nowrap px-3 py-2 text-left text-ink-muted"
                  >
                    {b}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {gosterilen.map((k) => (
                <tr key={k.personel_id} className="border-t border-rule">
                  <td className="px-3 py-2 text-ink">{k.ad_soyad}</td>
                  <td className="px-3 py-2">
                    <Sayi className="text-ink">{sayiBicimle(k.fazla_calisma_saat, 1)} sa</Sayi>
                  </td>
                  <td className="px-3 py-2">
                    <Sayi
                      className={cn(
                        'font-semibold',
                        k.kalan_kota_saat <= RISK_ESIGI ? 'text-signal' : 'text-ink-muted',
                      )}
                    >
                      {sayiBicimle(k.kalan_kota_saat, 1)} sa
                    </Sayi>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-ink-muted">
            {riskliler.length > 0
              ? `${riskliler.length} kişinin kalan kotası ${RISK_ESIGI} saatin altında.`
              : `Kimse sınıra yakın değil; en az kalanı olan ${gosterilen.length} kişi gösteriliyor.`}
          </p>
        </>
      )}
    </Kart>
  )
}

/** Ceza dökümü: ham değer, ağırlık, ağırlıklı ceza — ÜÇ AYRI SÜTUN.

    İkisinin tek sütunda gösterilmesi, toplamın satırların toplamı olmadığı
    bir tablo üretir (SDD 6.3.4). Hedefler kimlikleriyle değil ADLARIYLA
    listelenir; "S4" tek başına kimseye bir şey söylemez. */
function CezaDokumu({
  kalemler,
  toplam,
}: {
  kalemler: AnalizCezaKalemi[]
  toplam: number | null
}) {
  if (kalemler.length === 0) return null
  return (
    <Kart>
      <KartEtiketi>ceza dökümü</KartEtiketi>
      <table className="w-full min-w-[520px] border-collapse">
        <thead>
          <tr className="bg-sunken">
            {['HEDEF', 'HAM DEĞER', 'AĞIRLIK', 'AĞIRLIKLI CEZA'].map((b) => (
              <th key={b} className="mono-caps whitespace-nowrap px-3 py-2 text-left text-ink-muted">
                {b}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {kalemler.map((k) => (
            <tr key={k.kimlik} className="border-t border-rule">
              <td className="px-3 py-2 text-ink">
                {k.ad}
                <span className="ml-2 font-mono text-xs text-ink-muted">{k.kimlik}</span>
              </td>
              <td className="px-3 py-2">
                <Sayi className="text-ink-muted">{sayiBicimle(k.ham_deger, 1)}</Sayi>
              </td>
              <td className="px-3 py-2">
                <Sayi className="text-ink-muted">{sayiBicimle(k.agirlik, 0)}</Sayi>
              </td>
              <td className="px-3 py-2">
                <Sayi className="font-semibold text-ink">
                  {sayiBicimle(k.agirlikli_ceza, 0)}
                </Sayi>
              </td>
            </tr>
          ))}
          {toplam !== null && (
            <tr className="border-t-2 border-rule">
              <td className="px-3 py-2 font-semibold text-ink" colSpan={3}>
                TOPLAM
              </td>
              <td className="px-3 py-2">
                <Sayi className="font-semibold text-ink">{sayiBicimle(toplam, 0)}</Sayi>
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <p className="mt-3 text-xs text-ink-muted">
        Ham değer kuralın kendi biriminde ölçülür (kişi-saat, saat, gün); ağırlıklı ceza amaç
        fonksiyonuna girendir.
      </p>
    </Kart>
  )
}

/** Kümülatif adaletin vaadi sapmanın küçük olması değil, ZAMANLA küçülmesidir
    (Charter 5, K3). Bu kart o vaadin ölçüldüğü yer. */
function KumulatifDegisimKarti({ degisim }: { degisim: KumulatifDegisim }) {
  const { onceki_ortalama_sapma: onceki, simdiki_ortalama_sapma: simdiki } = degisim
  return (
    <Kart>
      <KartEtiketi>kümülatif değişim · önceki yayınlanmış döneme göre</KartEtiketi>
      {simdiki === null ? (
        <p className="text-sm text-ink-muted">Ölçüme giren personel yok.</p>
      ) : onceki === null ? (
        // SIFIR YAZILMAZ: "değişim olmadı" ile "karşılaştırılacak dönem yok"
        // aynı şey değildir.
        <p className="text-sm text-ink-muted">
          Karşılaştırılacak önceki yayınlanmış dönem yok. Bu dönemin ortalama gece sapması{' '}
          <Sayi className="text-ink">{sayiBicimle(simdiki, 2)} sa</Sayi>.
        </p>
      ) : (
        <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
          <span className="text-sm text-ink-muted">
            önceki <Sayi className="text-ink">{sayiBicimle(onceki, 2)} sa</Sayi>
          </span>
          <span className="text-sm text-ink-muted">
            şimdi <Sayi className="text-ink">{sayiBicimle(simdiki, 2)} sa</Sayi>
          </span>
          <span
            className={cn(
              'font-mono text-sm font-semibold',
              simdiki < onceki ? 'text-accent' : 'text-signal',
            )}
          >
            {simdiki < onceki ? '↓ azalıyor' : '↑ artıyor'} (
            {sapmaBicimle(simdiki - onceki)} sa)
          </span>
        </div>
      )}
    </Kart>
  )
}
