import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type {
  Analiz,
  CizelgeSurumu,
  GorevNoktasi,
  KapsamaAcigi,
  Musaitlik,
  Personel,
  Tercih,
  VardiyaTipi,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Kart, KartEtiketi, Rozet, Sayi } from '../components/app-ui'
import { bugunIso, gunKisaltmasiVeNumarasi, isoAyristir } from '../lib/tarih'
import { sayiBicimle } from '../lib/sayi'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
}

const SURUM_DURUM_METNI: Record<string, string> = {
  taslak: 'Taslak',
  cozuldu: 'Çözüldü',
  yayinlandi: 'Yayınlandı',
  arsiv: 'Arşiv',
}

const MUSAITLIK_TIP_METNI: Record<string, string> = {
  yillik_izin: 'İzin',
  rapor: 'Rapor',
  egitim: 'Eğitim',
  mazeret: 'Mazeret',
}

export function OzetEkrani({ ekranSec }: Props) {
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [kapsamaAcigi, setKapsamaAcigi] = useState<KapsamaAcigi[]>([])
  const [analiz, setAnaliz] = useState<Analiz | null>(null)
  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [noktalar, setNoktalar] = useState<GorevNoktasi[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])
  const [musaitlikler, setMusaitlikler] = useState<Musaitlik[]>([])
  const [tercihler, setTercihler] = useState<Tercih[]>([])
  const [hata, setHata] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.donemler(),
      api.personelListele(),
      api.noktaListele(),
      api.vardiyaTipiListele(),
      api.musaitlikListele(),
      api.tercihListele(),
    ])
      .then(([d, p, n, v, m, t]) => {
        setPersonelListesi(p)
        setNoktalar(n)
        setVardiyaTipleri(v)
        setMusaitlikler(m)
        setTercihler(t)
        if (d[0]) return api.surumler(d[0].donem_id)
        return []
      })
      .then((s) => setSurumler(s))
      .catch((e) => setHata(e instanceof Error ? e.message : 'Özet verisi yüklenemedi'))
  }, [])

  const sonSurum = surumler[0] ?? null

  useEffect(() => {
    if (!sonSurum) {
      setKapsamaAcigi([])
      setAnaliz(null)
      return
    }
    Promise.all([api.surumKapsamaAcigi(sonSurum.surum_id), api.analizGetir(sonSurum.surum_id)])
      .then(([k, a]) => {
        setKapsamaAcigi(k)
        setAnaliz(a)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Sürüm verisi yüklenemedi'))
  }, [sonSurum])

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )
  const noktaMap = useMemo(() => new Map(noktalar.map((n) => [n.nokta_id, n])), [noktalar])
  const vardiyaMap = useMemo(
    () => new Map(vardiyaTipleri.map((v) => [v.vardiya_tipi_id, v])),
    [vardiyaTipleri],
  )

  const toplamEksik = kapsamaAcigi.reduce((toplam, k) => toplam + k.eksik_sayi, 0)
  const kapsamaOrani = analiz ? Math.round(analiz.kapsama_orani * 100) : null

  const bekleyenTercihSayisi = tercihler.filter((t) => t.durum === 'beklemede').length

  const bugun = isoAyristir(bugunIso())
  const yaklasanMusaitlikler = [...musaitlikler]
    .filter((m) => isoAyristir(m.bitis_tarihi) >= bugun)
    .sort((a, b) => a.baslangic_tarihi.localeCompare(b.baslangic_tarihi))
    .slice(0, 6)

  return (
    <AppShell aktifEkran="Özet" ekranSec={ekranSec} baslik="Özet">
      {hata && <p className="text-sm text-signal">{hata}</p>}

      <div className="grid grid-cols-5 gap-4">
        <Kart>
          <KartEtiketi>kapsama</KartEtiketi>
          <Sayi className="text-sayi-buyuk font-semibold text-accent">
            {kapsamaOrani === null ? '—' : `%${kapsamaOrani}`}
          </Sayi>
        </Kart>
        <Kart>
          <KartEtiketi renk={toplamEksik > 0 ? 'warn' : undefined}>eksik hücre</KartEtiketi>
          <Sayi className={`text-sayi-buyuk font-semibold ${toplamEksik > 0 ? 'text-signal' : 'text-ink'}`}>
            {kapsamaAcigi.length}
          </Sayi>
        </Kart>
        <Kart>
          <KartEtiketi>toplam ceza</KartEtiketi>
          <Sayi className="text-sayi-buyuk font-semibold text-ink">
            {analiz?.toplam_ceza != null ? sayiBicimle(analiz.toplam_ceza, 0) : '—'}
          </Sayi>
        </Kart>
        <Kart>
          <KartEtiketi>bekleyen tercih</KartEtiketi>
          <p className="m-0 font-mono text-sayi-buyuk font-semibold text-ink">
            {bekleyenTercihSayisi} kişi
          </p>
        </Kart>
        <Kart>
          <KartEtiketi>sürüm durumu</KartEtiketi>
          <p className="m-0 font-mono text-sayi-buyuk font-semibold text-ink">
            {sonSurum ? `${SURUM_DURUM_METNI[sonSurum.durum] ?? sonSurum.durum} · S${sonSurum.surum_no}` : '—'}
          </p>
        </Kart>
      </div>

      <Kart>
        <div className="mb-4 flex items-baseline justify-between">
          <KartEtiketi>{sonSurum ? `açık uyarılar — sürüm ${sonSurum.surum_no}` : 'açık uyarılar'}</KartEtiketi>
          <span className="text-sm text-ink-muted">
            <Sayi>{kapsamaAcigi.length}</Sayi> kayıt
          </span>
        </div>
        {kapsamaAcigi.length === 0 ? (
          <p className="text-sm text-ink-muted">Açık uyarı yok.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-3 p-0">
            {kapsamaAcigi.slice(0, 8).map((k) => (
              <li key={k.acik_id} className="flex items-center gap-3 border-b border-rule pb-3 last:border-none">
                <span className="size-1.5 shrink-0 rounded-full bg-signal" />
                <span className="w-16 shrink-0 font-mono text-sm font-semibold text-ink">
                  {gunKisaltmasiVeNumarasi(k.tarih).toUpperCase()}
                </span>
                <Rozet varyant="notr" genislik={110}>
                  {noktaMap.get(k.nokta_id)?.ad ?? `Nokta ${k.nokta_id}`}
                </Rozet>
                <span className="text-sm text-ink-muted">
                  {k.eksik_sayi} eksik ({vardiyaMap.get(k.vardiya_tipi_id)?.ad ?? 'vardiya'})
                </span>
              </li>
            ))}
          </ul>
        )}
      </Kart>

      <Kart>
        <KartEtiketi>yaklaşan müsaitlik kayıtları</KartEtiketi>
        {yaklasanMusaitlikler.length === 0 ? (
          <p className="text-sm text-ink-muted">Yaklaşan kayıt yok.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-3 p-0">
            {yaklasanMusaitlikler.map((m) => (
              <li
                key={m.musaitlik_id}
                className="flex items-center gap-3 border-b border-rule pb-3 last:border-none"
              >
                <span className="w-32 shrink-0 text-sm font-medium text-ink">
                  {personelMap.get(m.personel_id)?.ad_soyad ?? `Personel ${m.personel_id}`}
                </span>
                <span className="font-mono text-sm text-ink-muted">
                  {gunKisaltmasiVeNumarasi(m.baslangic_tarihi)}
                  {m.baslangic_tarihi !== m.bitis_tarihi && ` – ${gunKisaltmasiVeNumarasi(m.bitis_tarihi)}`}
                </span>
                <Rozet varyant="notr" genislik={84}>
                  {MUSAITLIK_TIP_METNI[m.tip] ?? m.tip}
                </Rozet>
              </li>
            ))}
          </ul>
        )}
      </Kart>
    </AppShell>
  )
}
