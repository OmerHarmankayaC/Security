import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import type { DonemOzeti, Ufuk, Vardiyalarim } from '@/api/types'
import { Kart, KartEtiketi, Rozet } from '@/components/app-ui'
import { donemAraligiBicimle } from '@/lib/tarih'
import { sayiBicimle } from '@/lib/sayi'
import { cn } from '@/lib/utils'
import { useMetin } from '@/i18n/DilBaglami'
import { hataMetni } from '@/i18n/hata'
import type { Metinler } from '@/i18n/sozluk'

interface Props {
  veri: Vardiyalarim
}

// Eşik MUTLAK DEĞİL GÖRELİ: adalet ufkunda sayılar doksan günü kapsar ve
// sabit 0,5 saat herkesi "sapmış" gösterirdi. Taban 0,5 saat, dönem ufkunda
// önceki davranışı korur.
function esik(referans: number): number {
  return Math.max(0.5, Math.abs(referans) * 0.05)
}

function karsilastirmaMetni(
  sen: number,
  referans: number,
  birim: string,
  m: Metinler,
): string {
  const fark = sen - referans
  if (Math.abs(fark) < esik(referans)) return m.calisan.payinaYakinsin
  const buyukluk = sayiBicimle(Math.abs(fark), 1)
  return fark > 0
    ? m.calisan.payinUstundesin(buyukluk, birim)
    : m.calisan.payinAltindasin(buyukluk, birim)
}

function MetrikKarti({
  etiket,
  birim,
  sen,
  referans,
  ekip,
  ondalik = 0,
}: {
  etiket: string
  birim: string
  sen: number
  referans: number
  ekip: number
  ondalik?: number
}) {
  const m = useMetin()
  const fark = sen - referans
  const maks = Math.max(sen, referans, 1)
  return (
    <Kart>
      <div className="mb-4 flex items-center justify-between">
        <KartEtiketi>{etiket}</KartEtiketi>
        {Math.abs(fark) >= esik(referans) && (
          <Rozet varyant={fark > 0 ? 'kilitli' : 'notr'} genislik={192}>
            {fark > 0 ? m.calisan.adilPayinUstunde : m.calisan.adilPayinAltinda}
          </Rozet>
        )}
      </div>
      <p className="m-0 font-mono text-sayi-buyuk font-semibold text-ink">
        {sayiBicimle(sen, ondalik)} <span className="text-sm font-normal text-ink-muted">{birim}</span>
      </p>
      <div className="mt-4 flex flex-col gap-2">
        <BarSatiri etiket={m.calisan.sen} deger={sen} maks={maks} renk="bg-accent" ondalik={ondalik} />
        <BarSatiri etiket={m.calisan.adilPay} deger={referans} maks={maks} renk="bg-rule-strong" ondalik={ondalik} />
      </div>
      <p className="m-0 mt-2 text-sm text-ink-muted">
        {m.calisan.ekipOrtalamasi(sayiBicimle(ekip, 1))}
      </p>
    </Kart>
  )
}

function BarSatiri({
  etiket,
  deger,
  maks,
  renk,
  ondalik,
}: {
  etiket: string
  deger: number
  maks: number
  renk: string
  ondalik: number
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 etiket-caps text-ink-muted">{etiket}</span>
      <div className="h-2.5 flex-1 rounded-xs bg-sunken">
        <div
          className={`h-full rounded-xs ${renk}`}
          style={{ width: `${Math.min(100, (deger / maks) * 100)}%` }}
        />
      </div>
      {/* w-14: bu satır her zaman bir ondalık basamak yazar ve "Toplam Saat"
          üç haneli olabilir — "168,0" Azeret Mono 14px ile 45,5px sürer,
          eski w-10 (40px) taşıyordu. */}
      <span className="w-14 shrink-0 text-right font-mono text-sm text-ink">
        {sayiBicimle(deger, ondalik)}
      </span>
    </div>
  )
}

function UfukAnahtari({ ufuk, sec }: { ufuk: Ufuk; sec: (u: Ufuk) => void }) {
  const m = useMetin()
  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1" role="group" aria-label={m.calisan.olcumUfku}>
        {(
          [
            ['donem', m.calisan.buDonem],
            ['adalet', m.calisan.son90Gun],
          ] as const
        ).map(([deger, etiket]) => (
          <button
            key={deger}
            type="button"
            aria-pressed={ufuk === deger}
            onClick={() => sec(deger)}
            className={cn(
              'h-8 rounded-sm border px-3 text-sm',
              ufuk === deger
                ? 'border-accent bg-accent-soft font-medium text-accent'
                : 'border-rule bg-surface text-ink-muted',
            )}
          >
            {etiket}
          </button>
        ))}
      </div>
      <p className="m-0 text-sm text-ink-muted">
        {ufuk === 'donem'
          ? m.calisan.kapsamDonem
          : m.calisan.kapsamAdalet}
      </p>
    </div>
  )
}

function Ozet({ veri, ozet }: { veri: Vardiyalarim; ozet: DonemOzeti }) {
  const m = useMetin()
  const adilPayGece = ozet.adil_pay_gece ?? ozet.ekip_ortalama_gece
  const adilPayHaftaSonu = ozet.adil_pay_hafta_sonu ?? ozet.ekip_ortalama_hafta_sonu

  // SDD 5.7: uygun havuz (P_gece / P_hs) dışındaki çalışan o vardiyaları
  // yetkinliği gereği hiç alamaz; "adil payının altındasın" demek yanıltıcı
  // olur — o metrik hiç gösterilmez.
  const cumleler = [
    ozet.gece_havuzunda
      ? m.calisan.geceSaatinde(karsilastirmaMetni(ozet.gece_saati, adilPayGece, m.calisan.saat, m))
      : null,
    // "hafta sonlarında" bilerek "hafta sonunda" değil: aynı cümlede kart
    // etiketiyle (KartEtiketi "Hafta Sonu") aynı alt dizeyi taşısaydı,
    // ekran okuyucusu ve testler "Hafta Sonu" geçen iki ayrı öğeyi ayırt
    // edemezdi (bkz. test: havuz dışındaki karşılaştırmayı hiç göstermez).
    ozet.hafta_sonu_havuzunda
      ? m.calisan.haftaSonlarinda(
          karsilastirmaMetni(ozet.hafta_sonu_saati, adilPayHaftaSonu, m.calisan.saat, m),
        )
      : null,
    // Bulgu 1: toplam saat HER ZAMAN dönem içi (analiz_servisi.py bu turun
    // kapsamı dışında, ufuk almıyor) — adalet ufkunda bunu cümlenin
    // içinde açıkça söylemezsek "son 90 günde ... toplam saatte ..." okunuşu
    // sayının da 90 günü kapsadığını ima eder.
    ozet.ufuk === 'adalet'
      ? m.calisan.toplamSaatte(karsilastirmaMetni(ozet.toplam_saat, ozet.hedef_saat, m.calisan.saat, m))
      : m.calisan.toplamSaatte(karsilastirmaMetni(ozet.toplam_saat, ozet.hedef_saat, m.calisan.saat, m)),
  ].filter(Boolean)

  return (
    <>
      <div>
        {/* ozet.ufuk OKUNUR, yerel seçim durumu DEĞİL: ufuk değiştirildiğinde
            yeni yanıt gelene kadar burada hâlâ önceki isteğin ufku yazar.
            Aksi hâlde başlık "SON 90 GÜN" derken kartlar bu dönemin yedi
            gününü gösterebilir — ekrandaki sayının hangi ufka ait olduğu
            belirsizleşir (SDD 6.3.4). */}
        <p className="m-0 etiket-caps text-ink-muted">
          {ozet.ufuk === 'adalet'
            ? m.calisan.son90GunBaslik
            : veri.donem_baslangic_tarihi && veri.donem_bitis_tarihi
              ? m.calisan.donemBaslik(
                  donemAraligiBicimle(veri.donem_baslangic_tarihi, veri.donem_bitis_tarihi),
                )
              : ''}
        </p>
        <p className="m-0 mt-1 text-sm text-ink">
          {ozet.ufuk === 'adalet' ? m.calisan.cumleBasiAdalet : m.calisan.cumleBasiDonem}{' '}
          {cumleler.join(', ')}.
        </p>
      </div>

      {ozet.gece_havuzunda && (
        <MetrikKarti
          etiket={m.calisan.geceSaati}
          birim={m.calisan.saat}
          sen={ozet.gece_saati}
          referans={adilPayGece}
          ekip={ozet.ekip_ortalama_gece}
          ondalik={1}
        />
      )}
      {ozet.hafta_sonu_havuzunda && (
        <MetrikKarti
          etiket={m.calisan.haftaSonu}
          birim={m.calisan.saat}
          sen={ozet.hafta_sonu_saati}
          referans={adilPayHaftaSonu}
          ekip={ozet.ekip_ortalama_hafta_sonu}
          ondalik={1}
        />
      )}
      <MetrikKarti
        etiket={m.calisan.toplamSaat}
        birim={m.calisan.saat}
        sen={ozet.toplam_saat}
        referans={ozet.hedef_saat}
        ekip={ozet.ekip_ortalama_saat}
        ondalik={1}
      />

      {(!ozet.gece_havuzunda || !ozet.hafta_sonu_havuzunda) && (
        <p className="m-0 text-sm text-ink-muted">
          {!ozet.gece_havuzunda && !ozet.hafta_sonu_havuzunda
            ? m.calisan.ikisiDeYok
            : !ozet.gece_havuzunda
              ? m.calisan.geceYok
              : m.calisan.haftaSonuYok}
        </p>
      )}

      <p className="m-0 rounded-sm bg-sunken px-4 py-3 text-sm text-ink-muted">
        {m.calisan.yayindanHesaplanir}
      </p>
    </>
  )
}

export function DonemOzetimEkrani({ veri }: Props) {
  const m = useMetin()
  const [ufuk, setUfuk] = useState<Ufuk>('donem')
  const [ozet, setOzet] = useState<DonemOzeti | null>(null)
  const [yukleniyor, setYukleniyor] = useState(true)
  // Gerçek hata (ağ, 5xx, düşmüş oturum) MEŞRU `null` yanıtla (yayınlanmış
  // çizelge yok) KARIŞTIRILMAZ — ikisi de sessizce aynı "boş" duruma
  // düşerse, sunucu çökmüşken çalışan "henüz çizelge yok" okur.
  const [hata, setHata] = useState<string | null>(null)

  useEffect(() => {
    // İSTEK YARIŞI: ufuk hızla iki kez değişirse önceki isteğin GEÇ dönen
    // yanıtı yenisinin üstüne yazabilir. `guncel`, bu effect süperseded
    // olduğunda (bağımlılık değişip cleanup çalıştığında) false olur; o
    // andan sonra dönen yanıt/hata yok sayılır — React'in standart iptal
    // deseni, AbortController gerekmez.
    let guncel = true
    setYukleniyor(true)
    setHata(null)
    api
      .calisanOzetim(ufuk)
      .then((yanit) => {
        if (guncel) setOzet(yanit)
      })
      .catch((e) => {
        if (guncel) setHata(hataMetni(e, m))
      })
      .finally(() => {
        if (guncel) setYukleniyor(false)
      })
    return () => {
      guncel = false
    }
  }, [ufuk])

  return (
    <>
      <UfukAnahtari ufuk={ufuk} sec={setUfuk} />
      {hata ? (
        <Kart>
          <p className="m-0 text-sm text-signal">{hata}</p>
        </Kart>
      ) : yukleniyor && ozet === null ? null : ozet === null ? (
        <Kart>
          <p className="m-0 text-sm text-ink-muted">
            {m.calisan.ozetYok}
          </p>
        </Kart>
      ) : (
        <Ozet veri={veri} ozet={ozet} />
      )}
    </>
  )
}
