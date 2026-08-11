/**
 * Arayüzdeki BÜTÜN sayı biçimlemesinin tek kaynağı (Tasarım Referansı v4,
 * "Sayı biçimi").
 *
 * İki kural:
 *   1. Binlik ayracı YOKTUR — ne boşluk, ne nokta, ne virgül. `8240`, `10000`.
 *   2. Ondalık ayracı virgüldür — `3,39` · `0,61`. Türkçe kullanımına uyar.
 *
 * Öncesinde kodda iki ayrı yol vardı ve ikisi de yanlıştı: `toLocaleString('tr-TR')`
 * binlik ayracı olarak nokta koyuyordu (`8.240`), `toFixed()` ise ondalığı
 * İngilizce noktayla yazıyordu (`3.4`). Tek yardımcı ikisini de kapatır.
 *
 * CSV DIŞA AKTARMADA KULLANILMAZ. `lib/disaAktarma.ts` sayıları ham yazar:
 * dosyanın alan ayracı noktalı virgüldür ve Türkçe yerelli Excel virgülü
 * ondalık ayracı sayar; burada üretilen `8,5` o dosyada hücre sınırını
 * bulanıklaştırır. Ekran biçimi insanın, CSV biçimi tablo programınındır.
 */

/**
 * Ondalıksız biçimleyici. `Intl.NumberFormat` örneği her çağrıda yeniden
 * kurulmaz — kurulumu biçimlemenin kendisinden pahalıdır ve bu fonksiyon
 * Çizelge ızgarasında satır başına birden çok kez çağrılır.
 */
const TAM_SAYI = new Intl.NumberFormat('tr-TR', { useGrouping: false })

const ONDALIKLI = new Map<number, Intl.NumberFormat>()

function ondalikliBicimleyici(basamak: number): Intl.NumberFormat {
  let bicimleyici = ONDALIKLI.get(basamak)
  if (!bicimleyici) {
    bicimleyici = new Intl.NumberFormat('tr-TR', {
      useGrouping: false,
      minimumFractionDigits: basamak,
      maximumFractionDigits: basamak,
    })
    ONDALIKLI.set(basamak, bicimleyici)
  }
  return bicimleyici
}

/**
 * Sayıyı ekrana yazılacak biçime çevirir.
 *
 * `ondalik` verilmezse sayı olduğu gibi (gereksiz sıfır eklemeden) yazılır;
 * verilirse `toFixed` gibi tam o basamağa yuvarlanır ve sabitlenir — yan yana
 * dizilen değerlerin aynı basamakta durması sütun hizasının şartıdır.
 */
export function sayiBicimle(deger: number, ondalik?: number): string {
  if (!Number.isFinite(deger)) return '—'
  return ondalik === undefined
    ? TAM_SAYI.format(deger)
    : ondalikliBicimleyici(ondalik).format(deger)
}

const ISARETLI = new Map<number, Intl.NumberFormat>()

/**
 * İşaretli sapma: `+3,4` · `-1,2` · `0,0`.
 *
 * İşareti `signDisplay: 'exceptZero'` koyar, elle dize birleştirme değil —
 * eksi işaretinin hangi karakter olduğu (ASCII tire mi U+2212 mi) böylece
 * yerelin kararı olur ve iki ayrı yerde iki farklı karaktere ayrışmaz.
 * Sıfır işaretsizdir; "+0" sapma olmadığını değil, ölçülmediğini düşündürür.
 */
export function sapmaBicimle(deger: number, ondalik = 1): string {
  if (!Number.isFinite(deger)) return '—'
  let bicimleyici = ISARETLI.get(ondalik)
  if (!bicimleyici) {
    bicimleyici = new Intl.NumberFormat('tr-TR', {
      useGrouping: false,
      signDisplay: 'exceptZero',
      minimumFractionDigits: ondalik,
      maximumFractionDigits: ondalik,
    })
    ISARETLI.set(ondalik, bicimleyici)
  }
  return bicimleyici.format(deger)
}
