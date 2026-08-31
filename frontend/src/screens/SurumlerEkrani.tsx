import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
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
import { sayiBicimle } from '../lib/sayi'
import { useDil, useMetin } from '@/i18n/DilBaglami'
import { hataMetni } from '@/i18n/hata'
import { BOS } from '@/lib/sayi'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
}

const DURUM_VARYANTI: Record<CizelgeSurumuDurumu, 'dolu' | 'eksik' | 'kilitli' | 'notr'> = {
  taslak: 'kilitli',
  cozuldu: 'kilitli',
  yayinlandi: 'kilitli',
  arsiv: 'notr',
}

const SECIM_SINIFI =
  'h-8 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

export function SurumlerEkrani({ ekranSec, donemId, donemIdSec }: Props) {
  const { dil, metin: m } = useDil()
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
  // Silme onayı da aynı iki adımlı desende ve AYRI bir durumda: üç eylem
  // aynı satırda ve onayları birbirine karışmamalı.
  const [silmeOnayBekleyenId, setSilmeOnayBekleyenId] = useState<number | null>(null)
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
      .catch((e) => setHata(hataMetni(e, m)))
  }, [donemId, donemIdSec])

  const surumleriYukle = (id: number) => {
    api
      .surumler(id)
      .then(setSurumler)
      .catch((e) => setHata(hataMetni(e, m)))
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
      setHata(hataMetni(e, m))
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
      setHata(hataMetni(e, m))
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
      setHata(hataMetni(e, m))
    } finally {
      setIslenenId(null)
    }
  }

  const sil = async (surum: CizelgeSurumu) => {
    setIslenenId(surum.surum_id)
    setHata(null)
    try {
      await api.surumSil(surum.surum_id)
      setSilmeOnayBekleyenId(null)
      if (donemId !== null) surumleriYukle(donemId)
    } catch (e) {
      // Sunucunun metni OLDUĞU GİBİ gösterilir: üç ret nedeni var
      // (yayınlanmış, arşiv, zincire bağlı) ve hangisi olduğunu yalnızca
      // sunucu bilir.
      setHata(hataMetni(e, m))
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
      setHata(hataMetni(e, m))
    } finally {
      setKarsilastiriliyor(false)
    }
  }

  return (
    <AppShell
      aktifEkran="Sürümler"
      ekranSec={ekranSec}
      baslik={m.menu['Sürümler']}
      aksiyonlar={
        <Buton
          varyant={karsilastirmaAcik ? 'birincil' : 'ikincil'}
          onClick={() => setKarsilastirmaAcik((a) => !a)}
          disabled={surumler.length < 2}
        >
          {m.surumler.karsilastir}
        </Buton>
      }
    >
      {hata && <p className="m-0 text-sm text-signal">{hata}</p>}

      <div className="flex items-center gap-3">
        <label className="text-sm text-ink-muted">{m.surumler.donemEtiketi}</label>
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
            {m.surumler.surumSayisi(surumler.length)}
          </span>
        )}
      </div>

      {karsilastirmaAcik && (
        <Kart vurgulu>
          <KartEtiketi renk="accent">{m.surumler.karsilastirBasligi}</KartEtiketi>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">{m.surumler.oncekiSurum}</label>
              <select
                className={SECIM_SINIFI}
                value={oncekiId}
                onChange={(e) => setOncekiId(e.target.value)}
              >
                <option value="">{BOS}</option>
                {surumler.map((s) => (
                  <option key={s.surum_id} value={s.surum_id}>
                    {m.surumler.surumSecenegi(s.surum_no, m.surumDurumu[s.durum])}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-ink-muted">{m.surumler.yeniSurum}</label>
              <select
                className={SECIM_SINIFI}
                value={yeniId}
                onChange={(e) => setYeniId(e.target.value)}
              >
                <option value="">{BOS}</option>
                {surumler.map((s) => (
                  <option key={s.surum_id} value={s.surum_id}>
                    {m.surumler.surumSecenegi(s.surum_no, m.surumDurumu[s.durum])}
                  </option>
                ))}
              </select>
            </div>
            <Buton
              varyant="birincil"
              onClick={karsilastir}
              disabled={karsilastiriliyor || !oncekiId || !yeniId}
            >
              {karsilastiriliyor ? m.surumler.karsilastiriliyor : m.surumler.farklariGetir}
            </Buton>
          </div>
        </Kart>
      )}

      {karsilastirma && <KarsilastirmaSonucu sonuc={karsilastirma} />}

      {surumler.length === 0 ? (
        <Kart>
          <p className="m-0 text-sm text-ink-muted">{m.surumler.surumYok}</p>
        </Kart>
      ) : (
        surumler.map((s) => (
          <Kart key={s.surum_id}>
            <div className="flex items-center gap-6">
              <Rozet varyant={DURUM_VARYANTI[s.durum]} genislik={104}>
                {m.surumDurumu[s.durum]}
              </Rozet>
              <span className="w-24 shrink-0 text-sm font-semibold text-ink">
                {buyukHarf(m.surumler.surumNo(s.surum_no), dil)}
              </span>
              <Sayi className="w-32 shrink-0 text-sm text-ink-muted">
                {goreliZaman(s.olusturma_zamani)}
              </Sayi>
              <div className="w-28 shrink-0">
                <p className="m-0 etiket-caps text-ink-muted">
                  {buyukHarf('Toplam Ceza')}
                </p>
                <Sayi className="text-sayi-orta font-semibold text-ink">
                  {s.toplam_ceza === null ? BOS : sayiBicimle(Math.round(s.toplam_ceza))}
                </Sayi>
              </div>
              <div className="w-20 shrink-0">
                <p className="m-0 etiket-caps text-ink-muted">
                  {buyukHarf(m.surumler.acik, dil)}
                </p>
                <Sayi
                  className={cn(
                    'text-sayi-orta font-semibold',
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
                  <p className="m-0 etiket-caps text-ink-muted">
                    {buyukHarf('Fazla')}
                  </p>
                  <Sayi className="text-sayi-orta font-semibold text-signal">
                    {s.fazla_kadro_sayisi}
                  </Sayi>
                </div>
              )}
              <div className="ml-auto flex shrink-0 gap-2">
                {s.durum === 'yayinlandi' || s.durum === 'arsiv' ? (
                  <>
                    {/* İKİ EYLEM, İKİ AYRI İŞ — ve ayrım DÜĞMENİN ÜZERİNDE
                        okunmalı. Önceki adları ("Taslak Olarak Kopyala" /
                        "Taslak Türet") yan yana duruyordu, farkları yalnızca
                        ipucu metnindeydi ve kullanıcı yayınlanmış bir
                        çizelgeyi düzenlemek isterken boş taslağı açıyordu.
                        Düzenleme yolu FR-7.3'e göre KOPYADIR. */}
                    <Buton
                      varyant="birincil"
                      disabled={islenenId === s.surum_id}
                      title={m.surumler.kopyalaIpucu}
                      onClick={() => kopyaOnayiniAc(s)}
                    >
                      {m.surumler.kopyala}
                    </Buton>
                    <Buton
                      varyant="ikincil"
                      disabled={islenenId === s.surum_id}
                      title={m.surumler.bosTaslakIpucu}
                      onClick={() => taslakTuret(s)}
                    >
                      {m.surumler.bosTaslakAc}
                    </Buton>
                  </>
                ) : (
                  /* ATAMASIZ SÜRÜM YAYINLANAMAZ — arayüz koruması, sunucu
                     tarafı bilinçli olarak değiştirilmedi. Boş taslak (Tur 13)
                     açıp vazgeçen yönetici onun Yayınla düğmesine bastığında,
                     yayında duran DOLU sürüm arşive gidiyor ve çalışan
                     panelinde herkesin vardiyası kayboluyordu: onay metni
                     arşive alınacak sürümü söylüyor ama yenisinin BOŞ
                     olduğunu söylemiyor. Ayrım artık `atama_sayisi` ile
                     yapılabiliyor. */
                  <>
                    {/* Neden pasif olduğu YAZILI durur: ipucu yalnız fareyle
                        üzerine gelene görünür, pasif düğmenin tepkisizliği
                        ise hataya benziyor. */}
                    {s.atama_sayisi === 0 && (
                      <span className="self-center text-sm text-ink-muted">
                        {m.surumler.atamaYokYayinlanamaz}
                      </span>
                    )}
                    <Buton
                      varyant="birincil"
                      disabled={islenenId === s.surum_id || s.atama_sayisi === 0}
                      title={
                        s.atama_sayisi === 0
                          ? m.surumler.bosYayinUyarisi
                          : undefined
                      }
                      onClick={() => setOnayBekleyenId(s.surum_id)}
                    >
                      {m.surumler.yayinla}
                    </Buton>
                    {/* SİLME YALNIZ AÇIK SÜRÜMLERDE. Yayınlanmış ve arşiv
                        sürümler bu dalda zaten yok; sunucu da ayrıca
                        reddediyor — düğmenin gizlenmesi tek başına bir
                        koruma değil (SDD 5.5.2 ile aynı gerekçe). */}
                    <Buton
                      varyant="ikincil"
                      disabled={islenenId === s.surum_id}
                      title={m.surumler.silIpucu}
                      onClick={() => {
                        setOnayBekleyenId(null)
                        setKopyaOnayBekleyenId(null)
                        setSilmeOnayBekleyenId(s.surum_id)
                      }}
                    >
                      Sil
                    </Buton>
                  </>
                )}
              </div>
            </div>

            {silmeOnayBekleyenId === s.surum_id && (
              <div className="mt-4 flex items-center gap-4 border-t border-rule pt-4">
                <p className="m-0 flex-1 text-sm text-ink">
                  {m.surumler.silmeOnayi(
                    s.surum_no,
                    s.atama_sayisi > 0
                      ? m.surumler.atamaSayisi(s.atama_sayisi)
                      : m.surumler.atamalari,
                  )}{' '}
                  <span className="text-ink-muted">{m.surumler.silmeNotu}</span>
                </p>
                <Buton varyant="hayalet" onClick={() => setSilmeOnayBekleyenId(null)}>
                  {m.surumler.vazgec}
                </Buton>
                <Buton
                  varyant="birincil"
                  disabled={islenenId === s.surum_id}
                  onClick={() => sil(s)}
                >
                  {islenenId === s.surum_id ? 'Siliniyor…' : 'Onayla ve Sil'}
                </Buton>
              </div>
            )}

            {kopyaOnayBekleyenId === s.surum_id && (
              <div className="mt-4 flex items-center gap-4 border-t border-rule pt-4">
                <p className="m-0 flex-1 text-sm text-ink">
                  {/* Virgül şart: sürüm numarası ile atama sayısı ardışık iki
                      sayı ve aralarında ayraç olmadan "Sürüm 1 4 atamasıyla"
                      diye okunuyor. */}
                  {m.surumler.kopyaOnayi(
                    s.surum_no,
                    kopyalanacakAtamaSayisi !== null
                      ? m.surumler.kopyaAtamaSayisi(kopyalanacakAtamaSayisi)
                      : m.surumler.kopyaAtamalari,
                  )}{' '}
                  <span className="text-ink-muted">{m.surumler.kopyaNotu(s.surum_no)}</span>
                </p>
                <Buton varyant="hayalet" onClick={() => setKopyaOnayBekleyenId(null)}>
                  {m.surumler.vazgec}
                </Buton>
                <Buton
                  varyant="birincil"
                  disabled={islenenId === s.surum_id}
                  onClick={() => taslakOlarakKopyala(s)}
                >
                  {islenenId === s.surum_id ? m.surumler.kopyalaniyor : m.surumler.onaylaKopyala}
                </Buton>
              </div>
            )}

            {onayBekleyenId === s.surum_id && (
              <div className="mt-4 flex items-center gap-4 border-t border-rule pt-4">
                <p className="m-0 flex-1 text-sm text-ink">
                  {yayindaOlan
                    ? m.surumler.yayinOnayiArsiv(s.surum_no, yayindaOlan.surum_no)
                    : m.surumler.yayinOnayi(s.surum_no)}{' '}
                  <span className="text-ink-muted">{m.surumler.yayinNotu}</span>
                </p>
                <Buton varyant="hayalet" onClick={() => setOnayBekleyenId(null)}>
                  {m.surumler.vazgec}
                </Buton>
                <Buton
                  varyant="birincil"
                  disabled={islenenId === s.surum_id}
                  onClick={() => yayinla(s)}
                >
                  {islenenId === s.surum_id ? m.surumler.yayinlaniyor : m.surumler.onaylaYayinla}
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
  const m = useMetin()
  return (
    <Kart>
      <KartEtiketi>
        {m.surumler.farkBasligi(sonuc.onceki_surum_no, sonuc.yeni_surum_no, sonuc.toplam_degisiklik)}
      </KartEtiketi>

      <div className="mb-4 flex gap-8">
        <FarkSayaci etiket={m.surumler.fark.eklendi} deger={sonuc.eklenen} />
        <FarkSayaci etiket={m.surumler.fark.kaldirildi} deger={sonuc.kaldirilan} />
        <FarkSayaci etiket={m.surumler.fark.degisti} deger={sonuc.degisen} />
      </div>

      {sonuc.farklar.length === 0 ? (
        <p className="m-0 text-sm text-ink-muted">{m.surumler.farkYok}</p>
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-sunken">
              {m.surumler.farkSutunlari.map((b) => (
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
            {sonuc.farklar.map((f) => (
              <tr key={`${f.personel_id}-${f.tarih}`} className="border-t border-rule">
                <td className="px-3 py-2.5 text-sm text-ink">{f.ad_soyad}</td>
                <td className="px-3 py-2.5 font-mono text-sm text-ink-muted">
                  {gunKisaltmasiVeNumarasi(f.tarih)}
                </td>
                <td className="px-3 py-2.5">
                  <Rozet varyant={f.tur === 'kaldirildi' ? 'eksik' : 'kilitli'} genislik={96}>
                    {m.surumler.fark[f.tur]}
                  </Rozet>
                </td>
                <td className="px-3 py-2.5 text-sm text-ink-muted">
                  {f.onceki_blok ? `${f.onceki_blok} · ${f.onceki_nokta_ad ?? BOS}` : BOS}
                </td>
                <td className="px-3 py-2.5 text-sm text-ink">
                  {f.yeni_blok ? `${f.yeni_blok} · ${f.yeni_nokta_ad ?? BOS}` : BOS}
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
      <p className="m-0 etiket-caps text-ink-muted">
        {buyukHarf(etiket)}
      </p>
      <Sayi className="text-sayi-buyuk font-semibold text-ink">{deger}</Sayi>
    </div>
  )
}
