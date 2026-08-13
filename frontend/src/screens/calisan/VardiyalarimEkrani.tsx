import { useMemo } from 'react'
import type { KaldirilanGun, Vardiyalarim, Vardiyam } from '@/api/types'
import { Kart, KartEtiketi, Rozet, Sayi } from '@/components/app-ui'
import { buyukHarf } from '@/lib/metin'
import { sayiBicimle } from '@/lib/sayi'
import {
  bugunIso,
  gunEtiketi,
  gunKisaltmasiVeNumarasi,
  gunlerListesi,
  isoAyristir,
  tarihUzunBicim,
  zamanBicimle,
} from '@/lib/tarih'
import { aralikGradyani } from '@/lib/saatRengi'
import { baslangicSaati, blokEtiketi, blokSuresi } from '@/lib/blok'
import { cn } from '@/lib/utils'

interface Props {
  veri: Vardiyalarim
}

function saatAraligi(v: Vardiyam): string {
  return blokEtiketi(v.baslangic_zamani, v.bitis_zamani)
}

/**
 * Bloğun saat bandı — yönetici ızgarasıyla AYNI band (Tur 6 İş 3).
 *
 * Çalışan paneli önceki sürümde vardiyayı üç kategoriye ("Gündüz", "Akşam",
 * "Gece") vurup hücreyi o kategorinin rengiyle boyuyordu. Kategoriler blok
 * kataloğuyla birlikte kalktı (SRS TD-13); çalışanın gördüğü renk ile
 * yöneticinin gördüğü renk aynı fonksiyondan gelmek zorunda, aksi hâlde aynı
 * vardiya iki panelde farklı okunur.
 */
function bantZemini(baslangicZamani: string, bitisZamani: string): string {
  const bas = baslangicSaati(baslangicZamani)
  return aralikGradyani(bas, bas + blokSuresi(baslangicZamani, bitisZamani))
}

// Takvim ızgarası pazartesi ile başlar (TD-3'teki hafta sonu tanımı cumartesi/
// pazar olduğundan hafta sonu ızgaranın sağ ucunda bitişik durur).
const HAFTA_GUNLERI = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']

// JS getDay() pazar=0 verir; pazartesi=0 eksenine çeviriyoruz.
function pazartesiEksenliGun(iso: string): number {
  return (isoAyristir(iso).getDay() + 6) % 7
}

function sondakiBosHucreSayisi(gunler: string[]): number {
  const dolu = pazartesiEksenliGun(gunler[0]!) + gunler.length
  return (7 - (dolu % 7)) % 7
}

export function VardiyalarimEkrani({ veri }: Props) {
  const bugun = bugunIso()
  const vardiyaMap = useMemo(
    () => new Map(veri.vardiyalar.map((v) => [v.tarih, v])),
    [veri.vardiyalar],
  )
  const kaldirilanMap = useMemo(
    () => new Map(veri.kaldirilan_gunler.map((k) => [k.tarih, k])),
    [veri.kaldirilan_gunler],
  )

  // Liste görünümü vardiyaları ve kaldırılan günleri tarih sırasıyla birlikte
  // gösterir — kaldırılan bir gün, aradaki boşluk olarak değil kendi satırı
  // olarak görünmeli (FR-9.4: değişim üç türde ayrışır).
  const listeSatirlari = useMemo(() => {
    const satirlar: ({ tur: 'vardiya'; v: Vardiyam } | { tur: 'kaldirildi'; k: KaldirilanGun })[] =
      [
        ...veri.vardiyalar.map((v) => ({ tur: 'vardiya' as const, v })),
        ...veri.kaldirilan_gunler.map((k) => ({ tur: 'kaldirildi' as const, k })),
      ]
    return satirlar.sort((a, b) =>
      (a.tur === 'vardiya' ? a.v.tarih : a.k.tarih).localeCompare(
        b.tur === 'vardiya' ? b.v.tarih : b.k.tarih,
      ),
    )
  }, [veri.vardiyalar, veri.kaldirilan_gunler])

  if (veri.donem_id === null) {
    return (
      <Kart>
        <p className="m-0 text-sm text-ink-muted">Aktif bir planlama dönemi yok.</p>
      </Kart>
    )
  }

  if (!veri.yayinlanmis_surum_var) {
    return (
      <Kart>
        <p className="m-0 text-sm text-ink-muted">
          Bu dönem için henüz yayınlanmış bir çizelge yok.
        </p>
      </Kart>
    )
  }

  const gunler = gunlerListesi(veri.donem_baslangic_tarihi!, veri.donem_bitis_tarihi!)
  const degisenGunSayisi =
    veri.vardiyalar.filter((v) => v.degisim_tipi !== null).length + veri.kaldirilan_gunler.length

  return (
    <>
      {veri.siradaki && (
        <Kart>
          <p className="mb-4 etiket-caps text-ink-muted">{buyukHarf('Sıradaki Vardiyan')}</p>
          <p className="m-0 text-baslik-bolum font-semibold text-ink">
            {gunEtiketi(veri.siradaki.tarih, bugun)} · {tarihUzunBicim(veri.siradaki.tarih)}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Sayi className="text-sayi-buyuk font-semibold text-ink">
              {saatAraligi(veri.siradaki)}
            </Sayi>
            {/* Kart artık kategorinin rengiyle boyanmıyor: kategori yok.
                Bloğun kendi saat bandı, çalışmanın gecenin neresine düştüğünü
                kategoriden daha doğru söyler. */}
            <span
              className="h-4 w-28 rounded-xs border border-rule-strong"
              style={{
                backgroundImage: bantZemini(
                  veri.siradaki.baslangic_zamani,
                  veri.siradaki.bitis_zamani,
                ),
              }}
              aria-hidden="true"
            />
            {veri.siradaki.gece_saati > 0 && (
              <BeyazEtiket genislik={104}>{`${sayiBicimle(veri.siradaki.gece_saati, 0)} sa gece`}</BeyazEtiket>
            )}
            <BeyazEtiket genislik={110}>{veri.siradaki.nokta_ad}</BeyazEtiket>
          </div>
        </Kart>
      )}

      <Kart>
        <KartEtiketi>Dönem Görünümü · {gunler.length} Gün</KartEtiketi>
        <div className="grid grid-cols-7 gap-px overflow-hidden rounded-sm border border-rule bg-rule">
          {/* Başlıklar SABİT yedi sütundur, dönem uzunluğundan bağımsız —
              günler bu yedi sütuna sarmalanır (SDD 6.1: bir haftalık dönemde
              tek satır, dört haftalıkta dört satır). */}
          {HAFTA_GUNLERI.map((ad) => (
            <div
              key={`baslik-${ad}`}
              className="bg-sunken py-1.5 text-center etiket-caps text-ink-muted"
            >
              {buyukHarf(ad)}
            </div>
          ))}
          {/* Dönem haftanın ortasında başlıyorsa ilk satır doğru sütundan
              başlasın diye baştaki boş hücreler. */}
          {Array.from({ length: pazartesiEksenliGun(gunler[0]!) }, (_, i) => (
            <div key={`bos-bas-${i}`} className="bg-canvas" />
          ))}
          {gunler.map((g) => {
            const v = vardiyaMap.get(g)
            const kaldirilan = kaldirilanMap.get(g)
            const bugunMu = g === bugun
            // FR-9.4: üç değişim türü de ızgarada işaretlenir; hangi tür
            // olduğu liste görünümündeki rozetten okunur. Kaldırılan günde
            // hücre BOŞ kalır (artık vardiya yok) ve yalnızca işaret düşer.
            const degisimBasligi = kaldirilan
              ? 'Bu günkü vardiyan kaldırıldı'
              : v?.degisim_tipi === 'eklendi'
                ? 'Bu güne yeni vardiya eklendi'
                : v?.degisim_tipi === 'degisti'
                  ? 'Bu günkü vardiyan değişti'
                  : undefined
            return (
              <div
                key={g}
                className={cn(
                  'relative flex flex-col items-center gap-0.5 py-3 text-sm',
                  v ? 'bg-surface text-ink' : 'bg-surface text-ink-muted',
                  bugunMu && 'ring-2 ring-inset ring-accent',
                )}
                title={
                  v ? `${saatAraligi(v)} · ${v.nokta_ad}` : (degisimBasligi ?? undefined)
                }
              >
                <Sayi className="text-sayi-orta font-semibold">{g.slice(-2)}</Sayi>
                <span className="etiket-caps">
                  {v ? buyukHarf(v.nokta_ad.slice(0, 3)) : '–'}
                </span>
                {/* Hücrenin TAMAMINI boyamak yerine bloğun kendi bandı ince
                    bir şerit olarak altta durur: gün numarası ve nokta
                    kısaltması her hücrede aynı kontrastta okunur, band ise
                    çalışmanın hangi saatlere düştüğünü gösterir. */}
                {v && (
                  <span
                    className="mt-1 h-1.5 w-8 rounded-xs"
                    style={{
                      backgroundImage: bantZemini(v.baslangic_zamani, v.bitis_zamani),
                    }}
                    aria-hidden="true"
                  />
                )}
                {degisimBasligi && (
                  <span className="absolute inset-x-0 bottom-0 h-[3px] bg-accent" />
                )}
              </div>
            )
          })}
          {Array.from(
            { length: sondakiBosHucreSayisi(gunler) },
            (_, i) => <div key={`bos-son-${i}`} className="bg-canvas" />,
          )}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-ink-muted">
          {/* Kategorik lejant kalktı: üç kutu, üç sabit vardiya tipi
              olduğunda anlamlıydı. Band sürekli olduğundan gösterilecek şey
              bandın kendisidir. */}
          <span className="flex items-center gap-2">
            <span className="font-mono">00</span>
            <span
              className="h-3 w-20 rounded-xs border border-rule"
              style={{ backgroundImage: aralikGradyani(0, 24) }}
              aria-hidden="true"
            />
            <span className="font-mono">24</span>
            <span>saat bandı</span>
          </span>
          <LegendOgesi renk="bg-accent" etiket="Değişen gün" />
        </div>
      </Kart>

      <Kart>
        <KartEtiketi>Vardiya Listesi · {veri.vardiyalar.length} Vardiya</KartEtiketi>
        {listeSatirlari.length === 0 ? (
          <p className="m-0 text-sm text-ink-muted">Bu dönemde vardiyan yok.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col p-0">
            {listeSatirlari.map((satir) =>
              satir.tur === 'vardiya' ? (
                <ListeSatiri
                  key={`v-${satir.v.tarih}`}
                  tarih={satir.v.tarih}
                  bugun={bugun}
                  saatler={saatAraligi(satir.v)}
                  bant={bantZemini(satir.v.baslangic_zamani, satir.v.bitis_zamani)}
                  geceSaati={satir.v.gece_saati}
                  noktaAd={satir.v.nokta_ad}
                  isaretli={satir.v.degisim_tipi !== null}
                  rozet={
                    satir.v.degisim_tipi
                      ? satir.v.degisim_tipi === 'eklendi'
                        ? 'Eklendi'
                        : 'Değişti'
                      : null
                  }
                />
              ) : (
                // Kaldırılan gün: artık bir vardiya olmadığı için saat/nokta
                // üstü çizili ve soluk verilir — satırın kendisi durur, çünkü
                // "vardiyan alındı" en az yeni vardiya kadar önemli bir bilgi.
                <ListeSatiri
                  key={`k-${satir.k.tarih}`}
                  tarih={satir.k.tarih}
                  bugun={bugun}
                  saatler={blokEtiketi(
                    satir.k.onceki_baslangic_zamani,
                    satir.k.onceki_bitis_zamani,
                  )}
                  bant={bantZemini(
                    satir.k.onceki_baslangic_zamani,
                    satir.k.onceki_bitis_zamani,
                  )}
                  // Kaldırılan gün kaydı gece saatini taşımıyor; sayı yerine
                  // uydurulmuş bir değer göstermek yerine hiç gösterilmez.
                  geceSaati={null}
                  noktaAd={satir.k.onceki_nokta_ad}
                  isaretli
                  rozet="Kaldırıldı"
                  kaldirildi
                />
              ),
            )}
          </ul>
        )}
      </Kart>

      {veri.yayin_zamani && (
        <p className="m-0 rounded-sm bg-sunken px-4 py-3 text-sm text-ink-muted">
          Bu çizelge {zamanBicimle(veri.yayin_zamani)} tarihinde yayınlandı.
          {degisenGunSayisi > 0
            ? ` ${degisenGunSayisi} günün bir önceki sürüme göre değişti.`
            : ''}
        </p>
      )}
    </>
  )
}

// Vardiya listesinin tek satırı. Mobilde iki satıra yığılır (gün+etiket üstte,
// saat · vardiya · nokta altta) — tasarımdaki mobil sürüm böyle; tek satır
// 375px'e sığmıyor ve nokta adıyla rozeti kırpıyordu (NFR-7).
function ListeSatiri({
  tarih,
  bugun,
  saatler,
  bant,
  geceSaati,
  noktaAd,
  isaretli,
  rozet,
  kaldirildi = false,
}: {
  tarih: string
  bugun: string
  saatler: string
  /** Bloğun saat bandı (CSS gradient) — kategori adı değil. */
  bant: string
  /** Gece saati; kayıt taşımıyorsa `null` ve hiç gösterilmez. */
  geceSaati: number | null
  noktaAd: string
  isaretli: boolean
  rozet: string | null
  kaldirildi?: boolean
}) {
  const soluk = kaldirildi ? 'text-ink-muted' : 'text-ink'
  return (
    <li
      className={cn(
        'flex flex-col gap-1 border-t border-l-2 border-rule py-3 pl-3 first:border-t-0',
        'sm:flex-row sm:items-center sm:gap-4',
        isaretli ? 'border-l-accent' : 'border-l-transparent',
        kaldirildi && 'bg-canvas',
      )}
    >
      <div className="flex items-center gap-3 sm:contents">
        <Sayi className={cn('shrink-0 text-sm font-semibold sm:w-16', soluk)}>
          {gunKisaltmasiVeNumarasi(tarih)}
        </Sayi>
        <span className="shrink-0 text-sm text-ink-muted sm:w-16">{gunEtiketi(tarih, bugun)}</span>
        {rozet && (
          <span className="ml-auto sm:hidden">
            <Rozet varyant="kilitli" genislik={84}>
              {rozet}
            </Rozet>
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 sm:contents">
        {/* sm:w-28: "08:00-16:00" Azeret Mono 14px ile 100,1px sürüyor ve
            eski w-24'e (96px) sığmıyordu — sürüm 3'ün Mono'suyla 92px'ti. */}
        <Sayi className={cn('shrink-0 text-sm sm:w-28', soluk, kaldirildi && 'line-through')}>
          {saatler}
        </Sayi>
        <span className="flex shrink-0 items-center gap-2 sm:w-28">
          <span
            className={cn(
              'h-3 w-16 rounded-xs border border-rule-strong',
              kaldirildi && 'opacity-40',
            )}
            style={{ backgroundImage: bant }}
            aria-hidden="true"
          />
          {geceSaati !== null && geceSaati > 0 && (
            <span className="etiket-caps whitespace-nowrap text-ink-muted">
              {sayiBicimle(geceSaati, 0)} SA GECE
            </span>
          )}
        </span>
        <span className={cn('flex-1 truncate text-sm', soluk, kaldirildi && 'line-through')}>
          {noktaAd}
        </span>
      </div>
      {rozet && (
        <span className="hidden sm:block">
          <Rozet varyant="kilitli" genislik={84}>
            {rozet}
          </Rozet>
        </span>
      )}
    </li>
  )
}

function LegendOgesi({ renk, etiket }: { renk: string; etiket: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn('size-3 rounded-xs', renk)} />
      {etiket}
    </span>
  )
}

// "Sıradaki Vardiyan" kartı vardiyanın kendi renginde olduğundan (koyu/açık
// değişebilir), üzerindeki rozetler her zaman beyaz zeminle sabit kontrast
// sağlar — Rozet bileşeninin varyantları buradaki değişken zemine göre
// otomatik kontrast vermez.
function BeyazEtiket({ children, genislik }: { children: string; genislik: number }) {
  return (
    <span
      className="flex items-center justify-center rounded-sm bg-surface px-2.5 py-1 etiket-caps text-ink"
      style={{ width: genislik }}
    >
      {buyukHarf(children)}
    </span>
  )
}
