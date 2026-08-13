import type { Vardiyalarim } from '@/api/types'
import { Kart, KartEtiketi, Rozet } from '@/components/app-ui'
import { donemAraligiBicimle } from '@/lib/tarih'
import { sayiBicimle } from '@/lib/sayi'

interface Props {
  veri: Vardiyalarim
}

const ESIK = 0.5

function karsilastirmaMetni(sen: number, ekip: number, birim: string): string {
  const fark = sen - ekip
  if (Math.abs(fark) < ESIK) return `ortalamaya yakınsın`
  return fark > 0
    ? `ekip ortalamasının ${sayiBicimle(Math.abs(fark), 1)} ${birim} üzerindesin`
    : `ekip ortalamasının ${sayiBicimle(Math.abs(fark), 1)} ${birim} altındasın`
}

function MetrikKarti({
  etiket,
  birim,
  sen,
  ekip,
  ondalik = 0,
}: {
  etiket: string
  birim: string
  sen: number
  ekip: number
  ondalik?: number
}) {
  const fark = sen - ekip
  const maks = Math.max(sen, ekip, 1)
  return (
    <Kart>
      <div className="mb-4 flex items-center justify-between">
        <KartEtiketi>{etiket}</KartEtiketi>
        {Math.abs(fark) >= ESIK && (
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
        <BarSatiri etiket="EKİP ORT." deger={ekip} maks={maks} renk="bg-rule-strong" ondalik={ondalik} />
      </div>
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

export function DonemOzetimEkrani({ veri }: Props) {
  if (!veri.ozet || !veri.donem_baslangic_tarihi || !veri.donem_bitis_tarihi) {
    return (
      <Kart>
        <p className="m-0 text-sm text-ink-muted">
          Bu dönem için henüz yayınlanmış bir çizelge yok, özet hesaplanamıyor.
        </p>
      </Kart>
    )
  }

  const { ozet } = veri
  // SDD 5.7: uygun havuz (P_gece / P_hs) dışındaki çalışan o vardiyaları
  // yetkinliği gereği hiç alamaz; "ekip ortalamasının altındasın" demek
  // yanıltıcı olur — o metrik hiç gösterilmez.
  const cumleler = [
    ozet.gece_havuzunda
      ? `gece saatinde ${karsilastirmaMetni(ozet.gece_saati, ozet.ekip_ortalama_gece, 'saat')}`
      : null,
    ozet.hafta_sonu_havuzunda
      ? `hafta sonunda ${karsilastirmaMetni(ozet.hafta_sonu_saati, ozet.ekip_ortalama_hafta_sonu, 'saat')}`
      : null,
    `toplam saatte ${karsilastirmaMetni(ozet.toplam_saat, ozet.ekip_ortalama_saat, 'saat')}`,
  ].filter(Boolean)

  return (
    <>
      <div>
        <p className="m-0 etiket-caps text-ink-muted">
          {donemAraligiBicimle(veri.donem_baslangic_tarihi, veri.donem_bitis_tarihi)} DÖNEMİ
        </p>
        <p className="m-0 mt-1 text-sm text-ink">Bu dönemde {cumleler.join(', ')}.</p>
      </div>

      {ozet.gece_havuzunda && (
        <MetrikKarti etiket="Gece Saati" birim="saat" sen={ozet.gece_saati} ekip={ozet.ekip_ortalama_gece} ondalik={1} />
      )}
      {ozet.hafta_sonu_havuzunda && (
        <MetrikKarti etiket="Hafta Sonu" birim="saat" sen={ozet.hafta_sonu_saati} ekip={ozet.ekip_ortalama_hafta_sonu} ondalik={1} />
      )}
      <MetrikKarti etiket="Toplam Saat" birim="saat" sen={ozet.toplam_saat} ekip={ozet.ekip_ortalama_saat} ondalik={1} />

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
