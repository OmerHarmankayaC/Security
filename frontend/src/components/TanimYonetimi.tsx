import { useEffect, useState, type ReactNode } from 'react'
import { api } from '@/api/client'
import type { TanimKullanimi, TanimYolu } from '@/api/types'
import { Buton, Kart, KartEtiketi, Rozet } from '@/components/app-ui'
import { cn } from '@/lib/utils'

/**
 * Tanımlar ekranının beş varlığı (personel, yetkinlik, bina, görev noktası,
 * vardiya tipi) için ortak liste ve CRUD davranışı.
 *
 * Tek bileşen olmasının nedeni maddedeki "hepsi sağ üste, bütün alt
 * sayfalarda aynı konum ve aynı görünüm" koşulu: her sekme kendi eylem
 * çubuğunu çizerse konumlar zamanla ayrışır. Sekmeler yalnızca satırın
 * NASIL görüneceğini tarif eder, düzeni bu dosya kurar.
 *
 * Talep ve Kural sekmeleri bu düzenin dışındadır ve bilinçli olarak öyledir:
 * talep matrisinde satırlar görev noktalarından türer (eklenecek bağımsız
 * bir kayıt yoktur, hücreler yerinde düzenlenir), kural kataloğunda ise
 * H1–H8/S1–S8 kodda tanımlı sınıflarla eşleşir ve eklenip silinemez
 * (SDD 3.2.1).
 */
export interface TanimGorunumu<T> {
  /**
   * API yolu — silme ve kullanım sorgusu buradan geçer.
   *
   * İsteğe bağlı, çünkü `TanimListesi` onu hiç kullanmaz; yalnızca silme
   * yolu kullanır. Silinemeyen listeler (hesaplar: FR-10.5 gereği hesap
   * silinmez, devre dışı bırakılır) böylece aynı liste bileşenini uydurma
   * bir yol vermeden kullanabiliyor — kopyalanmış ikinci bir liste, iki
   * ekranın görünümünün zamanla ayrışması demekti.
   */
  yol?: TanimYolu
  kayitlar: T[]
  kimlik: (kayit: T) => number
  baslik: (kayit: T) => string
  /** Başlığın altındaki tek satırlık özet. */
  ozet: (kayit: T) => ReactNode
  /** Pasif kayıtlar listede ayırt edilir ve filtrelenebilir. */
  aktifMi: (kayit: T) => boolean
  /** Satırın sağ ucundaki ek rozet (ör. vardiya tipinde "Gece"). */
  ekRozet?: (kayit: T) => ReactNode
  /** Kayıt hiç yoksa gösterilecek açıklama. */
  bosMesaji?: ReactNode
}

/**
 * Görünüm tanımını tipini koruyarak kaydeder.
 *
 * Beş farklı kayıt tipi tek bir `Record` içinde toplanınca ortak tip
 * `unknown` olmak zorunda; ama tanımın İÇİNDEKİ geri çağırmalar kendi
 * tipleriyle yazılabilsin isteniyor (`(p: Personel) => p.ad_soyad`). Bu
 * fonksiyon o iki isteği birleştirir: çağrı yerinde tam denetim yapılır,
 * dışarı çıkarken tip silinir. Dönüşüm burada bir kez yazılır.
 */
export function gorunumKur<T>(gorunum: TanimGorunumu<T>): TanimGorunumu<unknown> {
  return gorunum as unknown as TanimGorunumu<unknown>
}

interface Props<T> {
  gorunum: TanimGorunumu<T>
  seciliId: number | null
  seciliIdDegistir: (id: number | null) => void
  pasifleriGoster: boolean
}

export function TanimListesi<T>({
  gorunum,
  seciliId,
  seciliIdDegistir,
  pasifleriGoster,
}: Props<T>) {
  const gorunenler = pasifleriGoster
    ? gorunum.kayitlar
    : gorunum.kayitlar.filter(gorunum.aktifMi)
  const gizlenenSayisi = gorunum.kayitlar.length - gorunenler.length

  if (gorunum.kayitlar.length === 0 && gorunum.bosMesaji) {
    return <p className="text-sm text-ink-muted">{gorunum.bosMesaji}</p>
  }

  return (
    <Kart>
      <ul className="m-0 flex list-none flex-col p-0">
        {gorunenler.map((kayit) => {
          const id = gorunum.kimlik(kayit)
          const aktif = gorunum.aktifMi(kayit)
          const secili = seciliId === id
          return (
            <li key={id} className="border-t border-rule first:border-none">
              <button
                type="button"
                aria-pressed={secili}
                onClick={() => seciliIdDegistir(secili ? null : id)}
                className={cn(
                  'flex w-full items-center justify-between gap-6 rounded-sm px-3 py-3 text-left transition-colors',
                  secili && 'bg-accent-soft',
                  // Pasif kayıt listede kalır ama geri çekilir — hem ayırt
                  // edilebilir olsun hem de aktiflerle karışmasın.
                  !aktif && 'opacity-60',
                )}
              >
                <div className="min-w-0">
                  <p className="m-0 truncate text-baslik-bolum font-medium text-ink">
                    {gorunum.baslik(kayit)}
                  </p>
                  <p className="m-0 mt-0.5 text-sm text-ink-muted">{gorunum.ozet(kayit)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {gorunum.ekRozet?.(kayit)}
                  <Rozet varyant={aktif ? 'dolu' : 'notr'} genislik={64}>
                    {aktif ? 'Aktif' : 'Pasif'}
                  </Rozet>
                </div>
              </button>
            </li>
          )
        })}
      </ul>
      {gizlenenSayisi > 0 && (
        <p className="mt-3 border-t border-rule pt-3 text-sm text-ink-muted">
          {gizlenenSayisi} pasif kayıt gizli.
        </p>
      )}
    </Kart>
  )
}

interface SilmeOnayiProps {
  yol: TanimYolu
  id: number
  ad: string
  onIptal: () => void
  onSilindi: () => void
}

/**
 * Silme onayı (madde 1).
 *
 * Onay istenmeden önce /kullanim sorulur, çünkü kullanıcıya sorulacak soru
 * kaydın kullanılıp kullanılmadığına göre DEĞİŞİR: kullanımdaki bir tanım
 * silinmez, pasifleştirilir. "Silinsin mi?" diye sorup pasifleştirmek,
 * kullanıcının onayladığı şeyden başkasını yapmak olurdu.
 */
export function SilmeOnayi({ yol, id, ad, onIptal, onSilindi }: SilmeOnayiProps) {
  const [kullanim, setKullanim] = useState<TanimKullanimi | null>(null)
  const [hata, setHata] = useState<string | null>(null)
  const [siliniyor, setSiliniyor] = useState(false)

  useEffect(() => {
    setKullanim(null)
    setHata(null)
    api
      .tanimKullanimi(yol, id)
      .then(setKullanim)
      .catch((e) => setHata(e instanceof Error ? e.message : 'Kullanım bilgisi alınamadı'))
  }, [yol, id])

  const sil = async () => {
    setSiliniyor(true)
    try {
      await api.tanimSil(yol, id)
      onSilindi()
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Silinemedi')
      setSiliniyor(false)
    }
  }

  const pasiflesecek = kullanim?.kullanimda_mi === true

  return (
    <Kart vurgulu>
      <KartEtiketi renk={pasiflesecek ? 'warn' : 'accent'}>
        {pasiflesecek ? 'pasifleştirme onayı' : 'silme onayı'}
      </KartEtiketi>
      {hata && <p className="text-sm text-signal">{hata}</p>}
      {!kullanim && !hata && <p className="text-sm text-ink-muted">Kullanım kontrol ediliyor…</p>}
      {kullanim && (
        <>
          <p className="m-0 text-sm text-ink">
            <span className="font-medium">{ad}</span>
            {pasiflesecek ? (
              <>
                {' '}
                {kullanim.kalemler.map((k) => `${k.sayi} ${k.kayit_turu}`).join(', ')} kaydında
                kullanılıyor. Kayıt <span className="font-medium">silinmeyecek</span>,
                pasifleştirilecek: yeni çözümlerde kullanılmaz, mevcut çizelgelerde görünmeye
                devam eder.
              </>
            ) : (
              <> hiçbir kayıtta kullanılmıyor. Kayıt kalıcı olarak silinecek.</>
            )}
          </p>
          <div className="mt-4 flex gap-2">
            <Buton varyant="birincil" onClick={sil} disabled={siliniyor}>
              {pasiflesecek ? 'Pasifleştir' : 'Kalıcı Olarak Sil'}
            </Buton>
            <Buton varyant="hayalet" onClick={onIptal} disabled={siliniyor}>
              Vazgeç
            </Buton>
          </div>
        </>
      )}
    </Kart>
  )
}
