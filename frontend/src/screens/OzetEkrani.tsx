import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type {
  Donem,
  Analiz,
  CizelgeSurumu,
  GorevNoktasi,
  KapsamaAcigi,
  Musaitlik,
  Personel,
  Tercih,
} from '../api/types'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { GunlukKapsamaSeridi } from '../components/GunlukKapsamaSeridi'
import { Buton, Kart, KartEtiketi, Rozet, Sayi } from '../components/app-ui'
import { bugunIso, donemAraligiBicimle, gunKisaltmasiVeNumarasi, isoAyristir } from '../lib/tarih'
import { sayiBicimle, sapmaBicimle } from '../lib/sayi'
import { sapmaEtiketi, sapmaGunu } from '@/lib/blok'
import { donemSec, olculebilirSurum } from '@/lib/donemSecimi'
import { cn } from '../lib/utils'

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

// EN ÇOK SAPAN ALTI KİŞİ. Analiz ekranındaki tam tabloya bakmak isteyen
// "Tümünü Analiz ekranında görüntüle" düğmesini kullanır — Özet ekranının
// sorusu "şu an ne oluyor", otuz kişilik bir tablo o soruyu boğar.
const KISI_BASINA_SAAT_SATIR_SAYISI = 6

export function OzetEkrani({ ekranSec }: Props) {
  const [surumler, setSurumler] = useState<CizelgeSurumu[]>([])
  const [kapsamaAcigi, setKapsamaAcigi] = useState<KapsamaAcigi[]>([])
  const [analiz, setAnaliz] = useState<Analiz | null>(null)
  const [personelListesi, setPersonelListesi] = useState<Personel[]>([])
  const [noktalar, setNoktalar] = useState<GorevNoktasi[]>([])
  const [musaitlikler, setMusaitlikler] = useState<Musaitlik[]>([])
  const [tercihler, setTercihler] = useState<Tercih[]>([])
  const [seciliDonem, setSeciliDonem] = useState<Donem | null>(null)
  // Şeritte seçili gün — açık listesinin süzgeci (bkz. GunlukKapsamaSeridi).
  // null iken liste BUGÜNÜ gösterir; ekranın sorusu "şu an ne oluyor".
  const [seciliGun, setSeciliGun] = useState<string | null>(null)
  const [hata, setHata] = useState<string | null>(null)

  useEffect(() => {
    function yukle() {
      Promise.all([
        api.donemler(),
        api.personelListele(),
        api.noktaListele(),
        api.musaitlikListele(),
        api.tercihListele(),
      ])
        .then(([d, p, n, m, t]) => {
          setPersonelListesi(p)
          setNoktalar(n)
          setMusaitlikler(m)
          setTercihler(t)
          // DÖNEM SEÇİMİ `d[0]` DEĞİL: uç nokta artan tarihe göre sıralı
          // döner ve ilk öğe EN ESKİ dönemdir. Kenar çubuğuyla aynı kuralı
          // kullanmak zorundayız, yoksa ekran bir dönemin başlığıyla başka
          // bir dönemin sayılarını gösterir (bkz. lib/donemSecimi.ts). Dönem
          // seçici EKLENMEZ: ekranın sorusu "şu an ne oluyor" ve dönem
          // bugünden türetilir.
          const donem = donemSec(d, bugunIso())
          setSeciliDonem(donem ?? null)
          if (donem) return api.surumler(donem.donem_id)
          return []
        })
        .then((s) => setSurumler(s))
        .catch((e) => setHata(e instanceof Error ? e.message : 'Özet verisi yüklenemedi'))
    }

    yukle()

    // TAZELEME: sekme arka planda kalıp geri geldiğinde veriler bayatlamış
    // olabilir ("şu an ne oluyor" sorusu tazelik ister). Sekme yeniden
    // görünür olduğunda yükleme fonksiyonu tekrar çağrılır.
    function gorunurlukDegisti() {
      if (document.visibilityState === 'visible') yukle()
    }
    document.addEventListener('visibilitychange', gorunurlukDegisti)
    return () => document.removeEventListener('visibilitychange', gorunurlukDegisti)
  }, [])

  // Çözülmemiş, ATAMASI OLMAYAN taslak ATLANIR: ölçüsü yoktur — %0 basmak
  // onu ölçülmüş gibi gösterirdi. Elle çizilen boş taslağın ataması vardır
  // ve bu ölçütle görünür (bkz. lib/donemSecimi.ts).
  const sonSurum = olculebilirSurum(surumler) ?? null
  const olculemeyenTaslak = sonSurum === null && surumler.length > 0

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

  // Sürüm değiştiğinde önceki sürümün gün süzgeci taşınmaz — o gün yeni
  // sürümde anlamsız olabilir.
  useEffect(() => {
    setSeciliGun(null)
  }, [sonSurum?.surum_id])

  const personelMap = useMemo(
    () => new Map(personelListesi.map((p) => [p.personel_id, p])),
    [personelListesi],
  )
  const noktaMap = useMemo(() => new Map(noktalar.map((n) => [n.nokta_id, n])), [noktalar])

  const toplamEksik = kapsamaAcigi.reduce((toplam, k) => toplam + k.eksik_sayi, 0)
  const kapsamaOrani = analiz ? Math.round(analiz.kapsama_orani * 100) : null

  const bekleyenTercihSayisi = tercihler.filter((t) => t.durum === 'beklemede').length

  // ARALIK METNİ — dönem seçici olmadığı için her aralık-bağlı blok hangi
  // aralığı gösterdiğini kendisi yazar (bkz. görev brief'i).
  const araligiMetni = seciliDonem
    ? donemAraligiBicimle(seciliDonem.baslangic_tarihi, seciliDonem.bitis_tarihi)
    : null

  const bugun = bugunIso()
  // Süzülen gün — seçili gün yoksa BUGÜN. Şeridin kendisi bunu bilmez
  // (bkz. GunlukKapsamaSeridi docstring'i): "hangi gün sorunlu" sorusunu o
  // yanıtlar, varsayılan günü ekran seçer.
  const gosterilenGun = seciliGun ?? bugun
  const gunlukAcikListesi = useMemo(
    () =>
      [...kapsamaAcigi]
        .filter((k) => sapmaGunu(k) === gosterilenGun)
        .sort((a, b) => a.baslangic_zamani.localeCompare(b.baslangic_zamani)),
    [kapsamaAcigi, gosterilenGun],
  )

  // KİŞİ BAŞINA SAAT — |sapma| azalan, ilk altı kişi (SDD 6.3.1).
  const enSapanAlti = useMemo(
    () =>
      [...(analiz?.saat_dagilimi ?? [])]
        .sort((a, b) => Math.abs(b.sapma) - Math.abs(a.sapma))
        .slice(0, KISI_BASINA_SAAT_SATIR_SAYISI),
    [analiz],
  )

  // BU DÖNEM MÜSAİT OLMAYANLAR — dönemle KESİŞEN kayıtlar. "Yaklaşan
  // müsaitlik kayıtları" kartından farklı: o bugünden ileriye bakar, bu kart
  // GÖSTERİLEN DÖNEMİ kapsayan kayıtları gösterir (dönem içinde kalmış ama
  // bugünden önce biten bir izin de burada görünür).
  const donemIciMusaitlikler = useMemo(() => {
    if (!seciliDonem) return []
    return musaitlikler
      .filter(
        (m) =>
          m.baslangic_tarihi <= seciliDonem.bitis_tarihi &&
          m.bitis_tarihi >= seciliDonem.baslangic_tarihi,
      )
      .sort((a, b) => a.baslangic_tarihi.localeCompare(b.baslangic_tarihi))
  }, [musaitlikler, seciliDonem])

  const bugunTarih = isoAyristir(bugun)
  const yaklasanMusaitlikler = [...musaitlikler]
    .filter((m) => isoAyristir(m.bitis_tarihi) >= bugunTarih)
    .sort((a, b) => a.baslangic_tarihi.localeCompare(b.baslangic_tarihi))
    .slice(0, 6)

  return (
    <AppShell
      aktifEkran="Özet"
      ekranSec={ekranSec}
      baslik="Özet"
      donemId={seciliDonem?.donem_id ?? null}
    >
      {hata && <p className="text-sm text-signal">{hata}</p>}
      {olculemeyenTaslak && (
        <p className="m-0 rounded-sm bg-sunken px-4 py-3 text-sm text-ink-muted">
          Bu dönemin son sürümü henüz boş bir taslak. Çizelge ekranından elle çizebilir ya da
          Çözüm ekranını kullanabilirsin.
        </p>
      )}

      {/* 1. ÖLÇÜ KARTLARI ŞERİDİ — üstteki satır hangi aralığa ait olduğunu
          söyler; dönem seçici yok, aralık bugünden türetilir. */}
      <div className="flex flex-col gap-3">
        {araligiMetni && <p className="m-0 text-sm text-ink-muted">{araligiMetni} dönemi için</p>}
        <div className="grid grid-cols-5 gap-4">
          <Kart>
            <KartEtiketi>kapsama</KartEtiketi>
            <Sayi className="text-sayi-buyuk font-semibold text-accent">
              {kapsamaOrani === null ? '—' : `%${kapsamaOrani}`}
            </Sayi>
          </Kart>
          <Kart>
            <KartEtiketi renk={toplamEksik > 0 ? 'warn' : undefined}>eksik hücre</KartEtiketi>
            <Sayi
              className={`text-sayi-buyuk font-semibold ${toplamEksik > 0 ? 'text-signal' : 'text-ink'}`}
            >
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
              {sonSurum
                ? `${SURUM_DURUM_METNI[sonSurum.durum] ?? sonSurum.durum} · S${sonSurum.surum_no}`
                : '—'}
            </p>
          </Kart>
        </div>
      </div>

      {/* 2. GÜNLÜK KAPSAMA KARTI — şerit "hangi gün sorunlu" sorusunu
          yanıtlar, altındaki liste "neden" sorusunu yanıtlar (bkz.
          GunlukKapsamaSeridi docstring'i). */}
      <Kart>
        <KartEtiketi>
          {araligiMetni ? `günlük kapsama · ${araligiMetni}` : 'günlük kapsama'}
        </KartEtiketi>
        {analiz && analiz.gunluk_kapsama.length > 0 ? (
          <GunlukKapsamaSeridi
            gunler={analiz.gunluk_kapsama}
            seciliTarih={seciliGun}
            gunSec={setSeciliGun}
          />
        ) : (
          <p className="text-sm text-ink-muted">Bu sürüm için günlük kapsama verisi yok.</p>
        )}

        <div className="mt-4">
          <div className="mb-2 flex items-baseline justify-between">
            <p className="m-0 text-sm text-ink-muted">
              {seciliGun
                ? `${gunKisaltmasiVeNumarasi(seciliGun)} günü açık kayıtları`
                : 'Bugünün açık kayıtları'}
            </p>
            <span className="text-sm text-ink-muted">
              <Sayi>{gunlukAcikListesi.length}</Sayi> kayıt
            </span>
          </div>
          {gunlukAcikListesi.length === 0 ? (
            <p className="text-sm text-ink-muted">Açık kayıt yok.</p>
          ) : (
            <ul className="m-0 flex list-none flex-col gap-3 p-0">
              {gunlukAcikListesi.map((k) => (
                <li
                  key={k.acik_id}
                  className="flex items-center gap-3 border-b border-rule pb-3 last:border-none"
                >
                  <span className="size-1.5 shrink-0 rounded-full bg-signal" />
                  <span className="w-24 shrink-0 text-sm font-medium text-ink">
                    {noktaMap.get(k.nokta_id)?.ad ?? `Nokta ${k.nokta_id}`}
                  </span>
                  <span className="text-sm text-ink-muted">
                    {k.eksik_sayi} eksik ({sapmaEtiketi(k)})
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Kart>

      {/* 3. KİŞİ BAŞINA SAAT — en çok sapan altı kişi; tam tablo Analiz
          ekranında. */}
      <Kart>
        <KartEtiketi>
          {araligiMetni ? `kişi başına saat · ${araligiMetni}` : 'kişi başına saat'}
        </KartEtiketi>
        {enSapanAlti.length === 0 ? (
          <p className="text-sm text-ink-muted">Bu sürümde saat sapması yok.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col p-0">
            {enSapanAlti.map((s) => (
              <li
                key={s.personel_id}
                className="flex items-center justify-between border-t border-rule py-2 text-sm first:border-none"
              >
                <span className="text-ink">{s.ad_soyad}</span>
                <span className="flex items-center gap-4 font-mono">
                  <Sayi className="text-ink-muted">{sayiBicimle(s.toplam_saat, 0)} sa</Sayi>
                  <Sayi
                    className={cn(
                      'font-semibold',
                      s.sapma > 0 ? 'text-signal' : s.sapma < 0 ? 'text-accent' : 'text-ink-muted',
                    )}
                  >
                    {sapmaBicimle(s.sapma, 1)} sa
                  </Sayi>
                </span>
              </li>
            ))}
          </ul>
        )}
        <Buton
          varyant="ikincil"
          className="mt-4"
          onClick={() => ekranSec('Analiz')}
          disabled={!sonSurum}
        >
          Tümünü Analiz ekranında görüntüle
        </Buton>
      </Kart>

      {/* 4. BU DÖNEM MÜSAİT OLMAYANLAR — dönemle KESİŞEN kayıtlar. */}
      <Kart>
        <KartEtiketi>
          {araligiMetni
            ? `bu dönem müsait olmayanlar · ${araligiMetni}`
            : 'bu dönem müsait olmayanlar'}
        </KartEtiketi>
        {donemIciMusaitlikler.length === 0 ? (
          <p className="text-sm text-ink-muted">Bu dönemde müsait olmayan yok.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-3 p-0">
            {donemIciMusaitlikler.map((m) => (
              <li
                key={m.musaitlik_id}
                className="flex items-center gap-3 border-b border-rule pb-3 last:border-none"
              >
                <span className="w-32 shrink-0 text-sm font-medium text-ink">
                  {personelMap.get(m.personel_id)?.ad_soyad ?? `Personel ${m.personel_id}`}
                </span>
                <span className="font-mono text-sm text-ink-muted">
                  {gunKisaltmasiVeNumarasi(m.baslangic_tarihi)}
                  {m.baslangic_tarihi !== m.bitis_tarihi &&
                    ` – ${gunKisaltmasiVeNumarasi(m.bitis_tarihi)}`}
                </span>
                <Rozet varyant="notr" genislik={84}>
                  {MUSAITLIK_TIP_METNI[m.tip] ?? m.tip}
                </Rozet>
              </li>
            ))}
          </ul>
        )}
      </Kart>

      {/* 5. YAKLAŞAN MÜSAİTLİK KAYITLARI — dönemle değil BUGÜNLE sınırlı;
          etiket bunu dürüstçe söyler. */}
      <Kart>
        <KartEtiketi>yaklaşan müsaitlik kayıtları · bugünden itibaren</KartEtiketi>
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
                  {m.baslangic_tarihi !== m.bitis_tarihi &&
                    ` – ${gunKisaltmasiVeNumarasi(m.bitis_tarihi)}`}
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
