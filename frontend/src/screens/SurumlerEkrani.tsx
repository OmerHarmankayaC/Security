import { useEffect, useMemo, useState } from 'react'
import { api, ApiHatasi } from '../api/client'
import type {
  CizelgeSurumu,
  CizelgeSurumuDurumu,
  Donem,
  SurumKarsilastirmasi,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, Kart, KartEtiketi, Rozet, Sayi } from '../components/app-ui'
import { buyukHarf } from '../lib/metin'
import { donemAraligiBicimle, gunKisaltmasiVeNumarasi, goreliZaman } from '../lib/tarih'
import { cn } from '../lib/utils'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
}

const DURUM_METNI: Record<CizelgeSurumuDurumu, string> = {
  taslak: 'Taslak',
  cozuldu: 'Çözüldü',
  yayinlandi: 'Yayınlandı',
  arsiv: 'Arşiv',
}

const DURUM_VARYANTI: Record<CizelgeSurumuDurumu, 'dolu' | 'eksik' | 'kilitli' | 'notr'> = {
  taslak: 'kilitli',
  cozuldu: 'kilitli',
  yayinlandi: 'kilitli',
  arsiv: 'notr',
}

const SECIM_SINIFI =
  'h-8 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

const FARK_ETIKETI = {
  eklendi: 'Eklendi',
  kaldirildi: 'Kaldırıldı',
  degisti: 'Değişti',
} as const

export function SurumlerEkrani({ ekranSec, donemId, donemIdSec }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [hata, setHata] = useState<string | null>(null)
  const [islenenId, setIslenenId] = useState<number | null>(null)
  // SDD 6.3.5: "Onay istenir." Uygulamanın hiçbir yerinde modal deseni yok
  // (tasarım referansında da yok), o yüzden onay satır içinde iki adımlı
  // yapılır: Yayınla → sonucu yazan bir şerit + Onayla / Vazgeç.
  const [onayBekleyenId, setOnayBekleyenId] = useState<number | null>(null)
  // Kopyalama onayı da aynı iki adımlı deseni izler. Ayrı bir durumda
  // tutulur: iki eylem aynı satırda ve onayları karışmamalı.
  const [kopyaOnayBekleyenId, setKopyaOnayBekleyenId] = useState<number | null>(null)
  // Onay metnindeki atama sayısı; onay açılınca çekilir. Sürüm listesi bu
  // sayıyı taşımıyor ve her satır için önden çekmek gereksiz istek olurdu.
  const [kopyalanacakAtamaSayisi, setKopyalanacakAtamaSayisi] = useState<number | null>(null)

  // Karşılaştırma paneli
  const [karsilastirmaAcik, setKarsilastirmaAcik] = useState(false)
  const [oncekiId, setOncekiId] = useState<string>('')
  const [yeniId, setYeniId] = useState<string>('')
  const [karsilastirma, setKarsilastirma] = useState<SurumKarsilastirmasi | null>(null)
  const [karsilastiriliyor, setKarsilastiriliyor] = useState(false)

  useEffect(() => {
    api
      .donemler()
      .then((d) => {
        setDonemler(d)
        if (donemId === null && d.length > 0) donemIdSec(d[0]!.donem_id)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Dönemler yüklenemedi'))
  }, [donemId, donemIdSec])

  const surumleriYukle = (id: number) => {
    api
      .surumler(id)
      .then(setSurumler)
      .catch((e) => setHata(e instanceof Error ? e.message : 'Sürümler yüklenemedi'))
  }

  useEffect(() => {
    if (donemId === null) return
    surumleriYukle(donemId)
    // Dönem değişince önceki dönemin sürümlerine ait karşılaştırma anlamsız kalır.
    setKarsilastirma(null)
    setOncekiId('')
    setYeniId('')
  }, [donemId])

  const donem = useMemo(
    () => donemler.find((d) => d.donem_id === donemId) ?? null,
    [donemler, donemId],
  )
  // TD-8: bir dönemde en fazla bir sürüm yayında olabilir; yayınlama onayı
  // arşive alınacak sürümü de adıyla söyler.
  const yayindaOlan = useMemo(
    () => surumler.find((s) => s.durum === 'yayinlandi') ?? null,
    [surumler],
  )

  const yayinla = async (surum: CizelgeSurumu) => {
    setIslenenId(surum.surum_id)
    setHata(null)
    try {
      await api.surumYayinla(surum.surum_id)
      setOnayBekleyenId(null)
      if (donemId !== null) surumleriYukle(donemId)
    } catch (e) {
      setHata(e instanceof ApiHatasi ? e.message : 'Sürüm yayınlanamadı')
    } finally {
      setIslenenId(null)
    }
  }

  const taslakTuret = async (surum: CizelgeSurumu) => {
    setIslenenId(surum.surum_id)
    setHata(null)
    try {
      await api.surumTaslakTuret(surum.surum_id)
      if (donemId !== null) surumleriYukle(donemId)
    } catch (e) {
      setHata(e instanceof ApiHatasi ? e.message : 'Taslak türetilemedi')
    } finally {
      setIslenenId(null)
    }
  }

  const kopyaOnayiniAc = async (surum: CizelgeSurumu) => {
    setOnayBekleyenId(null)
    setKopyaOnayBekleyenId(surum.surum_id)
    setKopyalanacakAtamaSayisi(null)
    setHata(null)
    try {
      setKopyalanacakAtamaSayisi((await api.surumAtamalari(surum.surum_id)).length)
    } catch {
      // Sayı yalnızca onay metnini somutlaştırır; alınamazsa onay metni
      // sayısız gösterilir, eylem engellenmez.
    }
  }

  const taslakOlarakKopyala = async (surum: CizelgeSurumu) => {
    setIslenenId(surum.surum_id)
    setHata(null)
    try {
      await api.surumTaslakOlarakKopyala(surum.surum_id)
      setKopyaOnayBekleyenId(null)
      if (donemId !== null) surumleriYukle(donemId)
    } catch (e) {
      setHata(e instanceof ApiHatasi ? e.message : 'Sürüm kopyalanamadı')
    } finally {
      setIslenenId(null)
    }
  }

  const karsilastir = async () => {
    if (!oncekiId || !yeniId) return
    setKarsilastiriliyor(true)
    setHata(null)
    try {
      setKarsilastirma(await api.surumKarsilastir(Number(oncekiId), Number(yeniId)))
    } catch (e) {
      setKarsilastirma(null)
      setHata(e instanceof Error ? e.message : 'Karşılaştırma yapılamadı')
    } finally {
      setKarsilastiriliyor(false)
    }
  }

  return (
    <AppShell
      aktifEkran="Sürümler"
      donemId={donemId}
      ekranSec={ekranSec}
      baslik="Sürümler"
      aksiyonlar={
        <Buton
          varyant={karsilastirmaAcik ? 'birincil' : 'ikincil'}
          onClick={() => setKarsilastirmaAcik((a) => !a)}
          disabled={surumler.length < 2}
        >
          Karşılaştır
        </Buton>
      }
    >
      {hata && <p className="m-0 text-sm text-signal">{hata}</p>}

      <div className="flex items-center gap-3">
        <label className="text-sm text-ink-muted">Dönem:</label>
        <select
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
        {donem && (
          <span className="font-mono text-xs text-ink-muted">
            {surumler.length} sürüm
          </span>
        )}
      </div>

      {karsilastirmaAcik && (
        <Kart vurgulu>
          <KartEtiketi renk="accent">sürüm karşılaştır</KartEtiketi>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Önceki sürüm</label>
              <select
                className={SECIM_SINIFI}
                value={oncekiId}
                onChange={(e) => setOncekiId(e.target.value)}
              >
                <option value="">—</option>
                {surumler.map((s) => (
                  <option key={s.surum_id} value={s.surum_id}>
                    Sürüm {s.surum_no} ({DURUM_METNI[s.durum]})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">Yeni sürüm</label>
              <select
                className={SECIM_SINIFI}
                value={yeniId}
                onChange={(e) => setYeniId(e.target.value)}
              >
                <option value="">—</option>
                {surumler.map((s) => (
                  <option key={s.surum_id} value={s.surum_id}>
                    Sürüm {s.surum_no} ({DURUM_METNI[s.durum]})
                  </option>
                ))}
              </select>
            </div>
            <Buton
              varyant="birincil"
              onClick={karsilastir}
              disabled={karsilastiriliyor || !oncekiId || !yeniId}
            >
              {karsilastiriliyor ? 'Karşılaştırılıyor…' : 'Farkları Getir'}
            </Buton>
          </div>
        </Kart>
      )}

      {karsilastirma && <KarsilastirmaSonucu sonuc={karsilastirma} />}

      {surumler.length === 0 ? (
        <Kart>
          <p className="m-0 text-sm text-ink-muted">Bu dönemde henüz sürüm yok.</p>
        </Kart>
      ) : (
        surumler.map((s) => (
          <Kart key={s.surum_id}>
            <div className="flex items-center gap-6">
              <Rozet varyant={DURUM_VARYANTI[s.durum]} genislik={92}>
                {DURUM_METNI[s.durum]}
              </Rozet>
              <span className="w-24 shrink-0 text-sm font-semibold text-ink">
                {buyukHarf(`Sürüm ${s.surum_no}`)}
              </span>
              <Sayi className="w-32 shrink-0 text-sm text-ink-muted">
                {goreliZaman(s.olusturma_zamani)}
              </Sayi>
              <div className="w-28 shrink-0">
                <p className="m-0 font-condensed text-[10px] tracking-[0.14em] text-ink-muted">
                  {buyukHarf('Toplam Ceza')}
                </p>
                <Sayi className="text-base font-semibold text-ink">
                  {s.toplam_ceza === null ? '—' : Math.round(s.toplam_ceza).toLocaleString('tr-TR')}
                </Sayi>
              </div>
              <div className="w-20 shrink-0">
                <p className="m-0 font-condensed text-[10px] tracking-[0.14em] text-ink-muted">
                  {buyukHarf('Açık')}
                </p>
                <Sayi
                  className={cn(
                    'text-base font-semibold',
                    s.kapsama_acigi_sayisi > 0 ? 'text-signal' : 'text-ink',
                  )}
                >
                  {s.kapsama_acigi_sayisi}
                </Sayi>
              </div>
              {/* Fazla kadro AYRI sütun: açıkla toplanmış tek bir sayı iki
                  zıt yöndeki sapmayı gizler ve "3 açık" ile "3 fazla" aynı
                  görünürdü. Sıfırsa gösterilmez — beklenen durum odur ve
                  her satıra bir sıfır koymak listeyi gürültüye boğardı. */}
              {s.fazla_kadro_sayisi > 0 && (
                <div className="w-20 shrink-0">
                  <p className="m-0 font-condensed text-[10px] tracking-[0.14em] text-ink-muted">
                    {buyukHarf('Fazla')}
                  </p>
                  <Sayi className="text-base font-semibold text-signal">
                    {s.fazla_kadro_sayisi}
                  </Sayi>
                </div>
              )}
              <div className="ml-auto flex shrink-0 gap-2">
                {s.durum === 'yayinlandi' || s.durum === 'arsiv' ? (
                  <>
                    <Buton
                      varyant="ikincil"
                      disabled={islenenId === s.surum_id}
                      title="Atamalarıyla birlikte kopyalar; kaynak sürüm değişmez"
                      onClick={() => kopyaOnayiniAc(s)}
                    >
                      Taslak Olarak Kopyala
                    </Buton>
                    <Buton
                      varyant="ikincil"
                      disabled={islenenId === s.surum_id}
                      title="Boş taslak açar; atamaları çözücü yazar"
                      onClick={() => taslakTuret(s)}
                    >
                      Taslak Türet
                    </Buton>
                  </>
                ) : (
                  <Buton
                    varyant="birincil"
                    disabled={islenenId === s.surum_id}
                    onClick={() => setOnayBekleyenId(s.surum_id)}
                  >
                    Yayınla
                  </Buton>
                )}
              </div>
            </div>

            {kopyaOnayBekleyenId === s.surum_id && (
              <div className="mt-4 flex items-center gap-4 border-t border-rule pt-4">
                <p className="m-0 flex-1 text-sm text-ink">
                  {/* Virgül şart: sürüm numarası ile atama sayısı ardışık iki
                      sayı ve aralarında ayraç olmadan "Sürüm 1 4 atamasıyla"
                      diye okunuyor. */}
                  Sürüm {s.surum_no},{' '}
                  {kopyalanacakAtamaSayisi !== null
                    ? `${kopyalanacakAtamaSayisi} atamasıyla birlikte`
                    : 'atamalarıyla birlikte'}{' '}
                  yeni bir taslak sürüme kopyalanacak.{' '}
                  <span className="text-ink-muted">
                    Sürüm {s.surum_no} olduğu gibi kalır — durumu değişmez, atamalarına
                    dokunulmaz. Düzenleme yeni taslak üzerinde yapılır.
                  </span>
                </p>
                <Buton varyant="hayalet" onClick={() => setKopyaOnayBekleyenId(null)}>
                  Vazgeç
                </Buton>
                <Buton
                  varyant="birincil"
                  disabled={islenenId === s.surum_id}
                  onClick={() => taslakOlarakKopyala(s)}
                >
                  {islenenId === s.surum_id ? 'Kopyalanıyor…' : 'Onayla ve Kopyala'}
                </Buton>
              </div>
            )}

            {onayBekleyenId === s.surum_id && (
              <div className="mt-4 flex items-center gap-4 border-t border-rule pt-4">
                <p className="m-0 flex-1 text-sm text-ink">
                  {yayindaOlan
                    ? `Sürüm ${s.surum_no} yayınlanacak, Sürüm ${yayindaOlan.surum_no} arşive alınacak.`
                    : `Sürüm ${s.surum_no} yayınlanacak.`}{' '}
                  <span className="text-ink-muted">
                    Yayınlanan sürüm salt okunur olur, üzerinde elle düzenleme yapılamaz.
                  </span>
                </p>
                <Buton varyant="hayalet" onClick={() => setOnayBekleyenId(null)}>
                  Vazgeç
                </Buton>
                <Buton
                  varyant="birincil"
                  disabled={islenenId === s.surum_id}
                  onClick={() => yayinla(s)}
                >
                  {islenenId === s.surum_id ? 'Yayınlanıyor…' : 'Onayla ve Yayınla'}
                </Buton>
              </div>
            )}
          </Kart>
        ))
      )}
    </AppShell>
  )
}

function KarsilastirmaSonucu({ sonuc }: { sonuc: SurumKarsilastirmasi }) {
  return (
    <Kart>
      <KartEtiketi>
        {`Sürüm ${sonuc.onceki_surum_no} → Sürüm ${sonuc.yeni_surum_no} · ${sonuc.toplam_degisiklik} değişen atama`}
      </KartEtiketi>

      <div className="mb-4 flex gap-8">
        <FarkSayaci etiket="Eklendi" deger={sonuc.eklenen} />
        <FarkSayaci etiket="Kaldırıldı" deger={sonuc.kaldirilan} />
        <FarkSayaci etiket="Değişti" deger={sonuc.degisen} />
      </div>

      {sonuc.farklar.length === 0 ? (
        <p className="m-0 text-sm text-ink-muted">İki sürüm arasında farklı atama yok.</p>
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-sunken">
              {['PERSONEL', 'GÜN', 'TÜR', 'ÖNCEKİ', 'YENİ'].map((b) => (
                <th
                  key={b}
                  className="whitespace-nowrap px-3 py-2 text-left font-condensed text-[10px] tracking-[0.1em] text-ink-muted"
                >
                  {b}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sonuc.farklar.map((f) => (
              <tr key={`${f.personel_id}-${f.tarih}`} className="border-t border-rule">
                <td className="px-3 py-2.5 text-sm text-ink">{f.ad_soyad}</td>
                <td className="px-3 py-2.5 font-mono text-sm text-ink-muted">
                  {gunKisaltmasiVeNumarasi(f.tarih)}
                </td>
                <td className="px-3 py-2.5">
                  <Rozet varyant={f.tur === 'kaldirildi' ? 'eksik' : 'kilitli'} genislik={84}>
                    {FARK_ETIKETI[f.tur]}
                  </Rozet>
                </td>
                <td className="px-3 py-2.5 text-sm text-ink-muted">
                  {f.onceki_vardiya_tipi_ad
                    ? `${f.onceki_vardiya_tipi_ad} · ${f.onceki_nokta_ad ?? '—'}`
                    : '—'}
                </td>
                <td className="px-3 py-2.5 text-sm text-ink">
                  {f.yeni_vardiya_tipi_ad
                    ? `${f.yeni_vardiya_tipi_ad} · ${f.yeni_nokta_ad ?? '—'}`
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Kart>
  )
}

function FarkSayaci({ etiket, deger }: { etiket: string; deger: number }) {
  return (
    <div>
      <p className="m-0 font-condensed text-[10px] tracking-[0.14em] text-ink-muted">
        {buyukHarf(etiket)}
      </p>
      <Sayi className="text-xl font-semibold text-ink">{deger}</Sayi>
    </div>
  )
}
