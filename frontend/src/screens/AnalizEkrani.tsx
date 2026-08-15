import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Analiz, CizelgeSurumu, Donem, Personel } from '../api/types'
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
      .analizGetir(surumId)
      .then(setAnaliz)
      .catch((e) => setHata(e instanceof Error ? e.message : 'Analiz yüklenemedi'))
      .finally(() => setYukleniyor(false))
  }, [surumId])

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
                  {saatSapmasiOlanlar
                    .sort((a, b) => Math.abs(b.sapma) - Math.abs(a.sapma))
                    .map((s) => (
                      <tr key={s.personel_id} className="border-t border-rule">
                        <td className="px-3 py-3 text-sm font-medium text-ink">{s.ad_soyad}</td>
                        <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                          {sayiBicimle(s.toplam_saat, 0)} sa
                        </td>
                        <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                          {sayiBicimle(s.hedef_saat, 0)} sa
                        </td>
                        <td
                          className={`px-3 py-3 font-mono text-sm font-semibold ${
                            Math.abs(s.sapma) > s.hedef_saat * 0.1 ? 'text-signal' : 'text-ink'
                          }`}
                        >
                          {saatSapmasi(s.sapma)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
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

  return (
    <Kart>
      <KartEtiketi>{etiket}</KartEtiketi>
      {satirlar.length === 0 ? (
        <p className="text-sm text-ink-muted">{bosMetin}</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {satirlar.map((s) => (
            <li key={s.personel_id} className="flex items-center gap-3 text-sm">
              <span className="w-32 shrink-0 truncate text-ink">{s.ad_soyad}</span>
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
      <p className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-px bg-ink" /> kişiye düşen adil pay (referans)
        </span>
        <span>{havuzAciklamasi}</span>
      </p>
    </Kart>
  )
}
