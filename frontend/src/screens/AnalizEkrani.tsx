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
import { sonDonem } from '@/lib/donemSecimi'
import { useMetin } from '@/i18n/DilBaglami'
import { SOZLUK, type Metinler } from '@/i18n/sozluk'
import { etkinDil } from '@/i18n/etkinDil'
import { hataMetni } from '@/i18n/hata'
import { BOS } from '@/lib/sayi'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
}

const SECIM_SINIFI =
  'h-8 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30 disabled:opacity-50'

function yuzdeBicimle(oran: number | null, m: Metinler): string {
  return oran === null ? BOS : m.yuzde(Math.round(oran * 100))
}

// Birim burada eklenir, sayının kendisi lib/sayi.ts'ten gelir — işaret ve
// ondalık ayracı kararı tek yerde durur.
function saatSapmasi(sapma: number): string {
  return `${sapmaBicimle(sapma, 1)} ${SOZLUK[etkinDil()].analiz.saatKisa}`
}

export function AnalizEkrani({ ekranSec, donemId, donemIdSec }: Props) {
  const m = useMetin()
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
        // `d[0]` EN ESKİ dönemdir (uç nokta artan tarihe sıralı döner);
        // varsayılan EN SON dönem olmalı (bkz. lib/donemSecimi.ts).
        if (donemId === null) {
          const son = sonDonem(d)
          if (son) donemIdSec(son.donem_id)
        }
      })
      .catch((e) => setHata(hataMetni(e, m)))
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
      .catch((e) => setHata(hataMetni(e, m)))
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
      .catch((e) => setHata(hataMetni(e, m)))
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

  // HEDEF ADLARI TEK KAYNAKTAN. Tablo `ceza_kalemleri`nin `ad` alanını
  // kullanıyordu, çubuk grafik ise ham `ceza_dokumu` sözlüğünün anahtarını —
  // aynı ekranda biri "Gece adaleti", diğeri "S2" yazıyordu. "S2" tek başına
  // kimseye bir şey söylemez.
  const hedefAdlari = useMemo(
    () => new Map((analiz?.ceza_kalemleri ?? []).map((k) => [k.kimlik, k.ad])),
    [analiz?.ceza_kalemleri],
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
      setHata(hataMetni(e, m))
    }
  }

  return (
    <AppShell
      aktifEkran="Analiz"
      ekranSec={ekranSec}
      baslik={m.menu['Analiz']}
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
                .catch(() => setHata(m.analiz.excelIndirilemedi))
                .finally(() => setExcelIniyor(false))
            }}
            disabled={surum === null || excelIniyor}
          >
            {excelIniyor ? m.analiz.indiriliyor : m.analiz.excel}
          </Buton>
          <Buton varyant="ikincil" onClick={disaAktar} disabled={surumId === null}>
            CSV
          </Buton>
        </>
      }
    >
      <Kart>
        <KartEtiketi>{m.analiz.secim}</KartEtiketi>
        <div className="flex flex-wrap items-end gap-6">
          <div className="flex flex-col gap-1">
            <label htmlFor="donem-sec" className="text-sm text-ink-muted">
              {m.analiz.donem}
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
              {m.analiz.surum}
            </label>
            <select
              id="surum-sec"
              className={SECIM_SINIFI}
              value={surumId ?? ''}
              onChange={(e) => setSurumId(e.target.value ? Number(e.target.value) : null)}
            >
              {surumler.map((s) => (
                <option key={s.surum_id} value={s.surum_id}>
                  {m.analiz.surumSecenegi(s.surum_no, m.surumDurumu[s.durum] ?? s.durum)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Kart>

      {hata && <p className="text-sm text-signal">{hata}</p>}
      {yukleniyor && <p className="text-sm text-ink-muted">{m.analiz.yukleniyor}</p>}

      {analiz && (
        <>
          {/* ALTI KART, ALTI SÜTUN. Beş sütunlu ızgarada altıncı kart
              ("toplam ceza") tek başına alt satıra düşüyordu: şerit tek bir
              okumaymış gibi durmuyor, ikinci satır ayrı bir bölüm gibi
              görünüyordu. Dar ekranda üçe, çok darda ikiye iner — sabit altı
              sütun 1280px altında kartları okunmaz genişliğe sıkıştırırdı. */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            <Kart>
              <KartEtiketi>{m.analiz.donemKapsamasi}</KartEtiketi>
              <p className="m-0 font-mono text-sayi-buyuk font-semibold text-accent">
                {yuzdeBicimle(analiz.kapsama_orani, m)}
              </p>
            </Kart>
            {/* Kapsama oranının YANINDA ama ondan ayrı: oran "talebin ne
                kadarı karşılandı" sorusunu yanıtlar; fazla kadro o soruya
                bir şey eklemez, fazla atama bir hücreyi daha iyi kapsamış
                olmaz (SRS 4.3 S1). */}
            <Kart>
              <KartEtiketi renk={analiz.toplam_fazla_kadro > 0 ? 'warn' : undefined}>
                {m.analiz.taleptenFazla}
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
                {m.analiz.karsilanmayan}
              </KartEtiketi>
              <p
                className={cn(
                  'm-0 font-mono text-sayi-buyuk font-semibold',
                  analiz.karsilanmayan_kisi_saat > 0 ? 'text-signal' : 'text-ink',
                )}
              >
                {sayiBicimle(analiz.karsilanmayan_kisi_saat, 0)}
                <span className="ml-1 font-sans text-sm font-normal text-ink-muted">{m.analiz.kisiSaat}</span>
              </p>
              <p className="m-0 text-sm text-ink-muted">
                {m.analiz.acikAralik(analiz.acik_aralik_sayisi)}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>{m.analiz.tercihKarsilama}</KartEtiketi>
              <p className="m-0 font-mono text-sayi-buyuk font-semibold text-ink">
                {yuzdeBicimle(analiz.tercih_karsilama_orani, m)}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>{m.analiz.enDengesiz}</KartEtiketi>
              <p className="m-0 text-sayi-buyuk font-semibold text-signal">
                {analiz.en_dengesiz_ad_soyad ?? BOS}
              </p>
            </Kart>
            <Kart>
              <KartEtiketi>{m.analiz.toplamCezaBasligi}</KartEtiketi>
              <Sayi className="text-sayi-buyuk font-semibold text-ink">
                {analiz.toplam_ceza !== null ? sayiBicimle(analiz.toplam_ceza, 0) : BOS}
              </Sayi>
            </Kart>
          </div>

          {/* UFUK ANAHTARI adalet kartlarının ÜSTÜNDE ve hangi ufkun seçili
              olduğu her zaman görünür: iki ufkun sayıları farklıdır ve
              belirsiz kalırsa tablo yanlış okunur (SDD 6.3.4). */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="mono-caps text-ink-muted">{m.analiz.olcumUfku}</span>
            <div className="flex gap-1" role="group" aria-label={m.analiz.olcumUfku}>
              {(
                [
                  ['donem', m.analiz.planlamaDonemi],
                  ['adalet', m.analiz.adaletUfku],
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
                ? m.analiz.ufukDonem
                : m.analiz.ufukAdalet}
            </span>
          </div>

          <AdaletGrafigi
            etiket={m.analiz.geceDagilimi}
            satirlar={geceSatirlari}
            cubukSinifi="bg-vardiya-gece"
            bosMetin={m.analiz.geceBos}
            havuzAciklamasi={m.analiz.geceHavuz}
          />

          <AdaletGrafigi
            etiket={m.analiz.haftaSonuDagilimi}
            satirlar={haftaSonuSatirlari}
            cubukSinifi="bg-accent"
            bosMetin={m.analiz.haftaSonuBos}
            havuzAciklamasi={m.analiz.haftaSonuHavuz}
          />

          <Kart>
            <KartEtiketi>{m.analiz.saatDengesi}</KartEtiketi>
            {saatSapmasiOlanlar.length === 0 ? (
              <p className="text-sm text-ink-muted">{m.analiz.herkesTutturdu}</p>
            ) : (
              <table className="w-full min-w-[560px] border-collapse">
                <thead>
                  <tr className="bg-sunken">
                    {/* Taban "HEDEF" değil ADİL PAYDIR (SRS S4): kişisel
                        sözleşme saati ulaşılabilir bir hedef olmadığından
                        herkes aynı yönde sapmalı görünüyor ve tablo hiçbir
                        ayrım üretmiyordu. Sütun adı da bunu söylemeli. */}
                    {m.analiz.saatSutunlari.map((b) => (
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
                        {sayiBicimle(s.toplam_saat, 0)} {m.analiz.saatKisa}
                      </td>
                      <td className="px-3 py-3 font-mono text-sm text-ink-muted">
                        {sayiBicimle(s.hedef_saat, 0)} {m.analiz.saatKisa}
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
                  ? m.analiz.ortakKayma(
                      ortancaSapma < 0 ? m.analiz.altinda : m.analiz.ustunde,
                      saatSapmasi(ortancaSapma),
                    )
                  : m.analiz.ortancaAciklamasi}
                {saatGizlenen > 0 && m.analiz.enUzaktakiler(saatDilimi.length)}
              </p>
            )}
          </Kart>

          {cezaGirdileri.length > 0 && (
            <Kart>
              <KartEtiketi>{m.analiz.cezaDokumu}</KartEtiketi>
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {cezaGirdileri.map(([kimlik, deger]) => (
                  <li key={kimlik} className="flex items-center gap-3 py-1 text-sm">
                    <span className="w-44 shrink-0 truncate text-ink-muted" title={kimlik}>
                      {hedefAdlari.get(kimlik) ?? kimlik}
                      <span className="ml-2 font-mono text-xs">{kimlik}</span>
                    </span>
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
              <KartEtiketi renk="warn">{m.analiz.binaDegisimi}</KartEtiketi>
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

          <KotaKarti satirlar={analiz.kota_durumu} yillikKota={analiz.yillik_kota_saat} />
          <CezaDokumu
            kalemler={analiz.ceza_kalemleri}
            toplam={analiz.toplam_ceza}
            kaynak={analiz.ceza_kaynagi}
          />
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
  const m = useMetin()
  // ÖLÇEK SAPMANIN AZAMİSİDİR, yükün değil. Çubuk adil paydan başlayıp iki
  // yana açıldığı için ölçülen şey uzaklıktır; yüke göre ölçeklenirse
  // sapmalar orantısız küçülür ve grafik ayırt ediciliğini kaybeder.
  const azamiSapma = satirlar.reduce((m, s) => Math.max(m, s.sapma), 0)
  // Yarım genişlik: merkez çizgisi ortada, her yan azami sapmayı taşır.
  const yariOran = (sapma: number) =>
    azamiSapma > 0 ? `${(sapma / azamiSapma) * 50}%` : '0%'

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
        <>
          {/* SÜTUN BAŞLIKLARI: üçüncü sayının ne olduğu fareyle üstüne
              gelmeden okunabilmeli. */}
          <div className="flex items-center gap-3 border-b border-rule pb-1.5 etiket-caps text-ink-muted">
            <span className="w-52 shrink-0">{m.analiz.personel}</span>
            <span className="flex-1 text-center">{m.analiz.adilPayaGore}</span>
            <span className="w-14 shrink-0 text-right">{m.analiz.yuk}</span>
            <span className="w-16 shrink-0 text-right">{m.analiz.adilPayKisa}</span>
            <span className="w-16 shrink-0 text-right">{m.analiz.sapma}</span>
          </div>
          <ul className="m-0 flex list-none flex-col gap-2 p-0 pt-2">
            {gosterilen.map((s) => (
              <li key={s.personel_id} className="flex items-center gap-3 text-sm">
                <span className="w-52 shrink-0 truncate text-ink" title={s.ad_soyad}>
                  {s.ad_soyad}
                </span>
                {/* IRAKSAYAN ÇUBUK: merkez adil pay, sağa taşan fazla almış,
                    sola taşan eksik. Bütün satırlar aynı eksenden başladığı
                    için kim ne kadar sapmış tek bakışta görünür; önceki
                    soldan dolan çubukta referans çizgisi çubuğun içinde
                    kayboluyordu. */}
                <span className="relative h-4 flex-1">
                  <span
                    className="absolute inset-y-0 left-1/2 w-px bg-rule-strong"
                    aria-hidden="true"
                  />
                  {s.yon !== 'yok' && (
                    <span
                      className={cn(
                        'absolute top-[3px] h-2.5 rounded-xs',
                        s.yon === 'ust' ? 'left-1/2 bg-signal' : 'right-1/2',
                        s.yon === 'alt' && cubukSinifi,
                      )}
                      style={{ width: yariOran(s.sapma) }}
                      aria-hidden="true"
                    />
                  )}
                </span>
                <Sayi className="w-14 shrink-0 text-right text-ink">
                  {sayiBicimle(s.saat, 0)} sa
                </Sayi>
                <Sayi className="w-16 shrink-0 text-right text-ink-muted">
                  {sayiBicimle(s.pay, 1)}
                </Sayi>
                {/* İŞARET yönü söyler; büyüklük çözücünün formülüdür ve ceza
                    dökümündeki sayıyla aynı kalır. */}
                <span
                  className="w-16 shrink-0 text-right"
                  title={
                    s.yon === 'yok'
                      ? m.analiz.bandIcinde
                      : m.analiz.cezalandirilanSapma(sayiBicimle(s.sapma, 0))
                  }
                >
                  <Sayi
                    className={cn(
                      'font-semibold',
                      s.yon === 'ust' && 'text-signal',
                      s.yon === 'alt' && 'text-ink',
                      s.yon === 'yok' && 'font-normal text-ink-muted',
                    )}
                  >
                    {s.yon === 'yok'
                      ? BOS
                      : `${s.yon === 'ust' ? '+' : '\u2212'}${sayiBicimle(s.sapma, 0)} sa`}
                  </Sayi>
                </span>
              </li>
            ))}
          </ul>
          <div className="flex justify-between pt-2 etiket-caps text-ink-muted">
            <span>{m.analiz.payinAltinda}</span>
            <span>adil pay</span>
            <span>{m.analiz.payinUstunde}</span>
          </div>
        </>
      )}
      {gizlenen > 0 && (
        <button
          type="button"
          onClick={() => setHepsi(true)}
          className="mt-3 font-mono text-sm text-accent underline-offset-2 hover:underline"
        >
          {m.analiz.dahaGoster(gizlenen)}
        </button>
      )}
      {hepsi && satirlar.length > ILK_GOSTERILEN && (
        <button
          type="button"
          onClick={() => setHepsi(false)}
          className="mt-3 font-mono text-sm text-ink-muted underline-offset-2 hover:underline"
        >
          {m.analiz.yalnizEnUzaktaki(ILK_GOSTERILEN)}
        </button>
      )}
      <p className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-px bg-ink" /> {m.analiz.referansAciklamasi}
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
    tabloda kimin sınıra yaklaştığı, tam liste basıldığında kaybolur.

    DEVİR AYRI SÜTUNDUR. Kalan kota yılın tamamından, "bu dönem" ise yalnız
    bu dönemden gelir; ikisi ayrılmadığında kotası devirden dolmuş kişi
    "0,0 sa fazla çalışma · 5,0 sa kalan" olarak görünüyordu. */
function KotaKarti({
  satirlar,
  yillikKota,
}: {
  satirlar: KotaDurumu[]
  yillikKota: number
}) {
  const m = useMetin()
  const RISK_ESIGI = 40
  const riskliler = satirlar.filter((k) => k.kalan_kota_saat <= RISK_ESIGI)
  const gosterilen = riskliler.length > 0 ? riskliler : satirlar.slice(0, 5)

  return (
    <Kart>
      <KartEtiketi renk={riskliler.length > 0 ? 'warn' : undefined}>
        {m.analiz.kotaBasligi}
      </KartEtiketi>
      {satirlar.length === 0 ? (
        <p className="text-sm text-ink-muted">Kota bilgisi yok.</p>
      ) : (
        <>
          <table className="w-full min-w-[520px] border-collapse">
            <thead>
              <tr className="bg-sunken">
                {m.analiz.kotaSutunlari.map((b) => (
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
                    <Sayi className="text-ink-muted">{sayiBicimle(k.devir_saat, 1)} sa</Sayi>
                  </td>
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
          {/* KARTIN ARİTMETİĞİ YAZILI OLMALI. Devir sütunu eklenene kadar
              kotası devirden dolmuş bir kişi "bu dönem 0,0 sa · kalan 5,0 sa"
              olarak görünüyordu ve satır hesap hatası gibi okunuyordu. */}
          <p className="mt-3 text-xs text-ink-muted">
            Yıllık kota {sayiBicimle(yillikKota, 0)} saat; kalan = kota − devir − bu dönem.
            {m.analiz.kotaNotu}
          </p>
          <p className="mt-1 text-xs text-ink-muted">
            {riskliler.length > 0
              ? m.analiz.kotaRiskli(riskliler.length, RISK_ESIGI)
              : m.analiz.kotaGuvenli(gosterilen.length)}
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
  kaynak,
}: {
  kalemler: AnalizCezaKalemi[]
  toplam: number | null
  kaynak: Analiz['ceza_kaynagi']
}) {
  const m = useMetin()
  if (kalemler.length === 0) return null
  return (
    <Kart>
      <KartEtiketi>{m.analiz.cezaDokumu}</KartEtiketi>
      <table className="w-full min-w-[520px] border-collapse">
        <thead>
          <tr className="bg-sunken">
            {m.analiz.dokumSutunlari.map((b) => (
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
        {m.analiz.dokumNotu}
        fonksiyonuna girendir.
        {/* Kaynak yazılmadan sayının nereden geldiği görünmez (Görev 5):
            "cozucu" ise döküm iş kaydından TAZE geldi; "kurallardan" ise
            sürüm çözücüsüz ya da bayat olduğu için döküm kural motorundan
            YENİDEN hesaplandı. "yok" durumunda kart zaten hiç render edilmez
            (kalemler boşsa fonksiyon en başta null döner). */}
        {kaynak === 'cozucu' && m.analiz.dokumCozucu}
        {kaynak === 'kurallardan' &&
          m.analiz.dokumKurallardan}
      </p>
    </Kart>
  )
}

/** Kümülatif adaletin vaadi sapmanın küçük olması değil, ZAMANLA küçülmesidir
    (Charter 5, K3). Bu kart o vaadin ölçüldüğü yer. */
function KumulatifDegisimKarti({ degisim }: { degisim: KumulatifDegisim }) {
  const m = useMetin()
  const { onceki_ortalama_sapma: onceki, simdiki_ortalama_sapma: simdiki } = degisim
  return (
    <Kart>
      <KartEtiketi>{m.analiz.geceAdaleti}</KartEtiketi>
      {simdiki === null ? (
        <p className="text-sm text-ink-muted">{m.analiz.olcumeGirenYok}</p>
      ) : onceki === null ? (
        // SIFIR YAZILMAZ: "değişim olmadı" ile "karşılaştırılacak dönem yok"
        // aynı şey değildir.
        <p className="text-sm text-ink-muted">
          {m.analiz.oncekiDonemYok}{' '}
          <Sayi className="text-ink">{sayiBicimle(simdiki, 2)} sa</Sayi>.
        </p>
      ) : (
        <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
          <span className="text-sm text-ink-muted">
            {m.analiz.onceki} <Sayi className="text-ink">{sayiBicimle(onceki, 2)} sa</Sayi>
          </span>
          <span className="text-sm text-ink-muted">
            {m.analiz.simdi} <Sayi className="text-ink">{sayiBicimle(simdiki, 2)} sa</Sayi>
          </span>
          <span
            className={cn(
              'font-mono text-sm font-semibold',
              // DEĞİŞMEDİ HÂLİ AYRI: eşitlik "artıyor" sayılıp alarm rengine
              // düşüyordu (önceki 4,07 · şimdi 4,07 · ↑ artıyor).
              simdiki === onceki
                ? 'text-ink-muted'
                : simdiki < onceki
                  ? 'text-accent'
                  : 'text-signal',
            )}
          >
            {simdiki === onceki ? m.analiz.degismedi : simdiki < onceki ? m.analiz.azaliyor : m.analiz.artiyor} (
            {sapmaBicimle(simdiki - onceki)} sa)
          </span>
        </div>
      )}
      {/* ÖLÇÜNÜN ADI KARTIN İÇİNDE OLMALI. Kart yalnız "önceki 4,07 · şimdi
          3,91" yazdığında iki sayının neyi ölçtüğü yalnız modeli bilene
          açıktı; ekranda anlamı olmayan bir sayı, olmayan sayıdan kötüdür. */}
      <p className="mt-3 text-xs text-ink-muted">
        {m.analiz.geceOlcuAciklamasi}
      </p>
    </Kart>
  )
}
