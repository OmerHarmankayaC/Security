import { useMemo } from 'react'
import type { Atama, GorevNoktasi, Personel } from '@/api/types'
import { blokEtiketi, gununParcalari, sapmaEtiketi, sapmaGunu } from '@/lib/blok'
import type { CizelgeVerisi } from '@/lib/disaAktarma'
import { aralikGradyani } from '@/lib/saatRengi'
import { buyukHarf, kisalt } from '@/lib/metin'
import {
  donemAraligiBicimle,
  gunlerListesi,
  haftaSonuMu,
  tarihBicimle,
  tarihUzunBicim,
} from '@/lib/tarih'
import { cn } from '@/lib/utils'
import { useDil } from '@/i18n/DilBaglami'

interface Props extends CizelgeVerisi {
  /** Başlıkta yazan üretim tarihi (ISO). Dışarıdan verilir; bileşen saat okumaz. */
  uretimTarihi: string
}

/**
 * Duvara asılan çizelge — GÜN IZGARASI, yatay A4 baskı için (SRS FR-8.8,
 * Tur 6 İş 5).
 *
 * ÇIKTI ARTIK SAAT EKSENİNDE. Önceki hâli personel × gün matrisiydi ve her
 * hücreye "08–16" sıkıştırıyordu: kâğıda bakan kişi bir bloğun ne zaman
 * başladığını okuyabiliyor ama günün hangi saatlerinin kimseyle
 * kapatılmadığını göremiyordu. Çalışma zamanı saat düzeyinde belirlendiğinden
 * (SRS TD-13) kâğıdın ekranla aynı çözünürlükte olması gerekir.
 *
 * BİÇİMLENDİRİCİ IZGARAYLA AYNI. Saat metni `blok.ts`ten, şeridin geometrisi
 * `gununParcalari`dan, renk bandı `saatRengi.ts`ten gelir — üçü de gün
 * ızgarasının kullandığı fonksiyonlardır. Baskı için ayrı bir kopya
 * çıkarılmaz; saat metni biçimleyicisinin üç kopyası bu projede bir kez
 * hataya yol açtı.
 *
 * SAYFA DÜZENİ. Her gün kendi ızgarasıdır ve yeni bir sayfada başlar; bir
 * günün personeli tek sayfaya sığmadığında tablo bölünür ve SAAT BAŞLIĞI
 * `thead` olduğu için her sayfada yeniden basılır (`.yazdirma-tablo`,
 * index.css). İkinci sayfadaki şeritler hangi saate denk geldiğini yoksa
 * kaybederdi.
 *
 * RENK TEK BAŞINA BİLGİ TAŞIMAZ — kâğıtta bu kural daha da bağlayıcıdır:
 * tarayıcı arka plan basmayı kapatabilir. Şeridin üzerinde saat aralığı ve
 * nokta kısaltması metin olarak durur; band yalnızca destekler.
 */
export function YazdirilabilirCizelge({
  donem,
  surum,
  atamalar,
  kapsamaAcigi,
  fazlaKadro,
  personelMap,
  noktaMap,
  uretimTarihi,
}: Props) {
  const { dil, metin: m } = useDil()
  const gunler = gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi)

  const personelAtamalari = useMemo(() => {
    const indeks = new Map<number, Atama[]>()
    for (const a of atamalar) {
      const mevcut = indeks.get(a.personel_id)
      if (mevcut) mevcut.push(a)
      else indeks.set(a.personel_id, [a])
    }
    return indeks
  }, [atamalar])

  const personeller = useMemo(() => {
    const idler = new Set(atamalar.map((a) => a.personel_id))
    return [...idler]
      .map((id) => personelMap.get(id))
      .filter((p): p is Personel => p !== undefined)
      .sort((a, b) => a.ad_soyad.localeCompare(b.ad_soyad, 'tr'))
  }, [atamalar, personelMap])

  const acikSatirlari = useMemo(
    () =>
      kapsamaAcigi
        .slice()
        .sort((a, b) => sapmaGunu(a).localeCompare(sapmaGunu(b)) || a.nokta_id - b.nokta_id),
    [kapsamaAcigi],
  )
  const toplamEksik = acikSatirlari.reduce((toplam, k) => toplam + k.eksik_sayi, 0)

  const fazlaSatirlari = useMemo(
    () =>
      fazlaKadro
        .slice()
        .sort((a, b) => sapmaGunu(a).localeCompare(sapmaGunu(b)) || a.nokta_id - b.nokta_id),
    [fazlaKadro],
  )
  const toplamFazla = fazlaSatirlari.reduce((toplam, f) => toplam + f.fazla_sayi, 0)

  return (
    <div className="yazdirma-alani bg-white text-black">
      <header className="mb-3 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-black pb-2">
        <h1 className="m-0 text-base font-semibold">
          {buyukHarf(m.yazdirma.baslik, dil)} ·{' '}
          {donemAraligiBicimle(donem.baslangic_tarihi, donem.bitis_tarihi)}
        </h1>
        {/* Sayılar mono, cümle değil: "… tarihinde üretildi" düz metindir ve
            Azeret Mono yalnızca sayı ve koda ayrılmıştır. */}
        <p className="m-0 text-[10px]">
          Sürüm <span className="font-mono">{surum.surum_no}</span> ·{' '}
          <span className="font-mono">{gunler.length}</span> {m.yazdirma.gun} ·{' '}
          <span className="font-mono">{personeller.length}</span> personel ·{' '}
          {m.yazdirma.uretildi(tarihBicimle(uretimTarihi))}
        </p>
      </header>

      {gunler.map((gun, sira) => (
        <GunSayfasi
          key={gun}
          gun={gun}
          ilkGun={sira === 0}
          personeller={personeller}
          personelAtamalari={personelAtamalari}
          noktaMap={noktaMap}
        />
      ))}

      <section className="yazdirma-sayfa-basi mt-4">
        <h2 className="m-0 mb-1 text-[9pt] font-semibold">{m.yazdirma.kapsamaAciklari}</h2>
        {acikSatirlari.length === 0 ? (
          // Bölüm hiç açık olmadığında da basılır. Gizlenirse okuyucu,
          // çıktının açıkları hiç göstermediği bir sürüm mü yoksa açığı
          // olmayan bir çizelge mi olduğunu ayırt edemez.
          <p className="m-0 text-[8pt]">{m.yazdirma.acikYok}</p>
        ) : (
          <>
            <p className="m-0 mb-1 text-[8pt]">
              {m.yazdirma.acikOzeti(acikSatirlari.length, toplamEksik)}
            </p>
            <table className="w-auto border-collapse">
              <thead>
                <tr>
                  {m.yazdirma.acikSutunlari.map((b) => (
                    <th
                      key={b}
                      className="border border-neutral-400 px-2 py-0.5 text-left text-[8pt] font-semibold"
                    >
                      {b}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {acikSatirlari.map((k) => (
                  <tr key={k.acik_id}>
                    <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                      {tarihBicimle(sapmaGunu(k))}
                    </td>
                    <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                      {sapmaEtiketi(k)}
                    </td>
                    <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                      {noktaMap.get(k.nokta_id)?.ad ?? '—'}
                    </td>
                    <td className="border border-neutral-400 px-2 py-0.5 text-right font-mono text-[8pt]">
                      {k.eksik_sayi}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>

      {/* Fazla kadro AYRI bir bolum: kapsama acigiyla ayni tabloya konsaydi
          iki zit yondeki sapma tek listede karisir. Bolum yalnizca sapma
          VARSA basilir — acik bolumunun yoklugu raporun asil vaadidir, fazla
          kadro ise beklenen durumun disinda bir olaydir. */}
      {fazlaSatirlari.length > 0 && (
        <section className="mt-4 break-inside-avoid">
          <h2 className="m-0 mb-1 text-[9pt] font-semibold">Talepten Fazla Kadro</h2>
          <p className="m-0 mb-1 text-[8pt]">
            {m.yazdirma.fazlaOzeti(fazlaSatirlari.length, toplamFazla)}
          </p>
          <table className="w-auto border-collapse">
            <thead>
              <tr>
                {m.yazdirma.fazlaSutunlari.map((b) => (
                  <th
                    key={b}
                    className="border border-neutral-400 px-2 py-0.5 text-left text-[8pt] font-semibold"
                  >
                    {b}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fazlaSatirlari.map((f) => (
                <tr key={f.fazla_id}>
                  <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                    {tarihBicimle(sapmaGunu(f))}
                  </td>
                  <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                    {sapmaEtiketi(f)}
                  </td>
                  <td className="border border-neutral-400 px-2 py-0.5 text-[8pt]">
                    {noktaMap.get(f.nokta_id)?.ad ?? '—'}
                  </td>
                  <td className="border border-neutral-400 px-2 py-0.5 text-right font-mono text-[8pt]">
                    {f.fazla_sayi}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}

/** Bir günün ızgarası. İlk gün dışındaki her gün yeni bir sayfada başlar. */
function GunSayfasi({
  gun,
  ilkGun,
  personeller,
  personelAtamalari,
  noktaMap,
}: {
  gun: string
  ilkGun: boolean
  personeller: readonly Personel[]
  personelAtamalari: Map<number, Atama[]>
  noktaMap: Map<number, GorevNoktasi>
}) {
  return (
    <section className={cn('mb-4', !ilkGun && 'yazdirma-sayfa-basi')}>
      <h2
        className={cn(
          'm-0 mb-1 text-[9pt] font-semibold',
          haftaSonuMu(gun) && 'bg-neutral-200 px-1',
        )}
      >
        {tarihUzunBicim(gun)}
        {haftaSonuMu(gun) && ' · hafta sonu'}
      </h2>
      <table className="yazdirma-tablo w-full table-fixed border-collapse">
        <colgroup>
          <col style={{ width: '110px' }} />
          {Array.from({ length: 24 }, (_, saat) => (
            <col key={saat} />
          ))}
        </colgroup>
        {/* SAAT BAŞLIĞI thead'dedir: tablo sayfaya bölündüğünde tarayıcı onu
            her sayfada yeniden basar. */}
        <thead>
          <tr>
            <th className="border border-neutral-400 px-1 py-0.5 text-left text-[7pt] font-semibold">
              Personel
            </th>
            {Array.from({ length: 24 }, (_, saat) => (
              <th
                key={saat}
                className="border border-neutral-400 px-0 py-0.5 text-center font-mono text-[6pt] font-semibold"
              >
                {String(saat).padStart(2, '0')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {personeller.map((p) => (
            <PersonelSatiri
              key={p.personel_id}
              gun={gun}
              personel={p}
              bloklar={personelAtamalari.get(p.personel_id) ?? []}
              noktaMap={noktaMap}
            />
          ))}
        </tbody>
      </table>
    </section>
  )
}

function PersonelSatiri({
  gun,
  personel,
  bloklar,
  noktaMap,
}: {
  gun: string
  personel: Personel
  bloklar: readonly Atama[]
  noktaMap: Map<number, GorevNoktasi>
}) {
  const parcalar = gununParcalari(bloklar, gun)
  // Gün toplamı, o gün BAŞLAYAN bloğun tamamıdır (SRS TD-1).
  const gunlukSaat = bloklar.filter((b) => b.tarih === gun).reduce((t, b) => t + b.sure_saat, 0)

  return (
    <tr>
      <td className="border border-neutral-400 px-1 py-0.5 text-[7pt] whitespace-nowrap">
        {personel.ad_soyad}
        {gunlukSaat > 0 && <span className="font-mono"> · {gunlukSaat}sa</span>}
      </td>
      <td className="relative border border-neutral-400 p-0" colSpan={24}>
        {/* Saat ayraçları: şeridin altında, üç saatte bir. */}
        <div className="pointer-events-none absolute inset-0 flex" aria-hidden="true">
          {Array.from({ length: 24 }, (_, saat) => (
            <span
              key={saat}
              className={cn('h-full flex-1', saat % 3 === 0 && 'border-l border-neutral-300')}
            />
          ))}
        </div>
        {/* Satır yüksekliğini şeritler değil bu boşluk belirler — mutlak
            konumlu şeritler yükseklik üretmez. */}
        <div className="h-[13pt]" />
        {parcalar.map(({ blok, parca }) => {
          const uzunluk = parca.bitis - parca.baslangic
          const metin = `${parca.oncekiGundenGeliyor ? '‹' : ''}${blokEtiketi(
            blok.baslangic_zamani,
            blok.bitis_zamani,
          )} ${kisalt(noktaMap.get(blok.nokta_id)?.ad ?? '')}${
            parca.sonrakiGuneTasiyor ? '›' : ''
          }`
          // DAR ŞERİDİN ETİKETİ DIŞARI TAŞAR. "22.00–05.00 GÜV" 6pt Mono ile
          // yaklaşık dört saat genişliğinde yer kaplıyor; iki saatlik bir
          // parçanın içine sığmayınca kırpılıyor ve kâğıtta "22.00–05.00 G…"
          // kalıyordu — üstelik gece yarısını aşan bloğun `›` işareti de tam
          // o kırpmanın içinde kayboluyordu. Ekranda ipucu metni bu kaybı
          // telafi eder, kâğıtta telafi edecek bir şey yok.
          //
          // Eşik ölçüye göre: dört saatten dar parçalarda metin şeridin
          // yanına konur. Gün sonuna dayanmış bir parçada sağda yer
          // kalmadığı için sola yazılır.
          const dar = uzunluk < 4
          const solaYaz = dar && parca.bitis > 20
          return (
            <div key={blok.atama_id}>
              <div
                className={cn(
                  'absolute inset-y-[1px] flex items-center justify-center overflow-hidden border border-neutral-500',
                  parca.oncekiGundenGeliyor && 'border-l-0',
                  parca.sonrakiGuneTasiyor && 'border-r-0',
                )}
                style={{
                  left: `${(parca.baslangic / 24) * 100}%`,
                  width: `${(uzunluk / 24) * 100}%`,
                  backgroundImage: aralikGradyani(parca.baslangic, parca.bitis),
                }}
              >
                {/* Metin şeridin bilgisidir; band yalnızca destekler. Tarayıcı
                    arka plan basmıyorsa kâğıtta kalan tek şey budur. */}
                {!dar && (
                  <span className="truncate bg-white/80 px-0.5 font-mono text-[6pt] leading-none">
                    {metin}
                  </span>
                )}
              </div>
              {dar && (
                <span
                  className="pointer-events-none absolute inset-y-0 flex items-center px-0.5 font-mono text-[6pt] leading-none whitespace-nowrap"
                  style={
                    solaYaz
                      ? { right: `${((24 - parca.baslangic) / 24) * 100}%` }
                      : { left: `${(parca.bitis / 24) * 100}%` }
                  }
                >
                  {metin}
                </span>
              )}
            </div>
          )
        })}
      </td>
    </tr>
  )
}
