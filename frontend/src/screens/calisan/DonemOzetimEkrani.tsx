import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import type { DonemOzeti, Ufuk, Vardiyalarim } from '@/api/types'
import { Kart, KartEtiketi, Rozet } from '@/components/app-ui'
import { donemAraligiBicimle } from '@/lib/tarih'
import { sayiBicimle } from '@/lib/sayi'
import { cn } from '@/lib/utils'

interface Props {
  veri: Vardiyalarim
}

// Eşik MUTLAK DEĞİL GÖRELİ: adalet ufkunda sayılar doksan günü kapsar ve
// sabit 0,5 saat herkesi "sapmış" gösterirdi. Taban 0,5 saat, dönem ufkunda
// önceki davranışı korur.
function esik(referans: number): number {
  return Math.max(0.5, Math.abs(referans) * 0.05)
}

function karsilastirmaMetni(sen: number, referans: number, birim: string): string {
  const fark = sen - referans
  if (Math.abs(fark) < esik(referans)) return 'ortalamaya yakınsın'
  return fark > 0
    ? `adil payının ${sayiBicimle(Math.abs(fark), 1)} ${birim} üzerindesin`
    : `adil payının ${sayiBicimle(Math.abs(fark), 1)} ${birim} altındasın`
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
  const fark = sen - referans
  const maks = Math.max(sen, referans, 1)
  return (
    <Kart>
      <div className="mb-4 flex items-center justify-between">
        <KartEtiketi>{etiket}</KartEtiketi>
        {Math.abs(fark) >= esik(referans) && (
          <Rozet varyant={fark > 0 ? 'kilitli' : 'notr'} genislik={192}>
            {fark > 0 ? 'Ortalamanın Üstünde' : 'Ortalamanın Altında'}
          </Rozet>
        )}
      </div>
      <p className="m-0 font-mono text-sayi-buyuk font-semibold text-ink">
        {sayiBicimle(sen, ondalik)} <span className="text-sm font-normal text-ink-muted">{birim}</span>
      </p>
      <div className="mt-4 flex flex-col gap-2">
        <BarSatiri etiket="SEN" deger={sen} maks={maks} renk="bg-accent" ondalik={ondalik} />
        <BarSatiri etiket="ADİL PAY" deger={referans} maks={maks} renk="bg-rule-strong" ondalik={ondalik} />
      </div>
      <p className="m-0 mt-2 text-sm text-ink-muted">ekip ortalaması {sayiBicimle(ekip, 1)} sa</p>
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
  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1" role="group" aria-label="Ölçüm ufku">
        {(
          [
            ['donem', 'Bu Dönem'],
            ['adalet', 'Son 90 Gün'],
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
          ? 'Sayılar yalnızca bu dönemi kapsar.'
          : 'Sayılar son doksan günü kapsar; geçmiş yayınlanmış çizelgeler dahil.'}
      </p>
    </div>
  )
}

function Ozet({ veri, ozet }: { veri: Vardiyalarim; ozet: DonemOzeti }) {
  const adilPayGece = ozet.adil_pay_gece ?? ozet.ekip_ortalama_gece
  const adilPayHaftaSonu = ozet.adil_pay_hafta_sonu ?? ozet.ekip_ortalama_hafta_sonu

  // SDD 5.7: uygun havuz (P_gece / P_hs) dışındaki çalışan o vardiyaları
  // yetkinliği gereği hiç alamaz; "adil payının altındasın" demek yanıltıcı
  // olur — o metrik hiç gösterilmez.
  const cumleler = [
    ozet.gece_havuzunda
      ? `gece saatinde ${karsilastirmaMetni(ozet.gece_saati, adilPayGece, 'saat')}`
      : null,
    // "hafta sonlarında" bilerek "hafta sonunda" değil: aynı cümlede kart
    // etiketiyle (KartEtiketi "Hafta Sonu") aynı alt dizeyi taşısaydı,
    // ekran okuyucusu ve testler "Hafta Sonu" geçen iki ayrı öğeyi ayırt
    // edemezdi (bkz. test: havuz dışındaki karşılaştırmayı hiç göstermez).
    ozet.hafta_sonu_havuzunda
      ? `hafta sonlarında ${karsilastirmaMetni(ozet.hafta_sonu_saati, adilPayHaftaSonu, 'saat')}`
      : null,
    `toplam saatte ${karsilastirmaMetni(ozet.toplam_saat, ozet.hedef_saat, 'saat')}`,
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
            ? 'SON 90 GÜN'
            : veri.donem_baslangic_tarihi && veri.donem_bitis_tarihi
              ? `${donemAraligiBicimle(veri.donem_baslangic_tarihi, veri.donem_bitis_tarihi)} DÖNEMİ`
              : ''}
        </p>
        <p className="m-0 mt-1 text-sm text-ink">
          {ozet.ufuk === 'adalet' ? 'Son 90 günde' : 'Bu dönemde'} {cumleler.join(', ')}.
        </p>
      </div>

      {ozet.gece_havuzunda && (
        <MetrikKarti
          etiket="Gece Saati"
          birim="saat"
          sen={ozet.gece_saati}
          referans={adilPayGece}
          ekip={ozet.ekip_ortalama_gece}
          ondalik={1}
        />
      )}
      {ozet.hafta_sonu_havuzunda && (
        <MetrikKarti
          etiket="Hafta Sonu"
          birim="saat"
          sen={ozet.hafta_sonu_saati}
          referans={adilPayHaftaSonu}
          ekip={ozet.ekip_ortalama_hafta_sonu}
          ondalik={1}
        />
      )}
      <MetrikKarti
        etiket="Toplam Saat"
        birim="saat"
        sen={ozet.toplam_saat}
        referans={ozet.hedef_saat}
        ekip={ozet.ekip_ortalama_saat}
        ondalik={1}
      />

      {(!ozet.gece_havuzunda || !ozet.hafta_sonu_havuzunda) && (
        <p className="m-0 text-sm text-ink-muted">
          {!ozet.gece_havuzunda && !ozet.hafta_sonu_havuzunda
            ? 'Görev noktanda gece ve hafta sonu vardiyası bulunmadığı için bu iki karşılaştırma gösterilmiyor.'
            : !ozet.gece_havuzunda
              ? 'Görev noktanda gece vardiyası bulunmadığı için gece karşılaştırması gösterilmiyor.'
              : 'Görev noktanda hafta sonu vardiyası bulunmadığı için hafta sonu karşılaştırması gösterilmiyor.'}
        </p>
      )}

      <p className="m-0 rounded-sm bg-sunken px-4 py-3 text-sm text-ink-muted">
        Sayılar yalnızca yayınlanmış çizelgeden hesaplanır. Yönetici üzerinde çalıştığı taslak buraya
        yansımaz.
      </p>
    </>
  )
}

export function DonemOzetimEkrani({ veri }: Props) {
  const [ufuk, setUfuk] = useState<Ufuk>('donem')
  const [ozet, setOzet] = useState<DonemOzeti | null>(null)
  const [yukleniyor, setYukleniyor] = useState(true)

  useEffect(() => {
    setYukleniyor(true)
    api
      .calisanOzetim(ufuk)
      .then(setOzet)
      .catch(() => setOzet(null))
      .finally(() => setYukleniyor(false))
  }, [ufuk])

  return (
    <>
      <UfukAnahtari ufuk={ufuk} sec={setUfuk} />
      {yukleniyor && ozet === null ? null : ozet === null ? (
        <Kart>
          <p className="m-0 text-sm text-ink-muted">
            Bu dönem için henüz yayınlanmış bir çizelge yok, özet hesaplanamıyor.
          </p>
        </Kart>
      ) : (
        <Ozet veri={veri} ozet={ozet} />
      )}
    </>
  )
}
