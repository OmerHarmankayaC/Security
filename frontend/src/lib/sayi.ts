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
import { YEREL, type Dil } from '@/i18n/diller'


/**
 * Değeri olmayan hücrenin yerine yazılan işaret.
 *
 * Uzun tire (—) kullanılmıyor: arayüzün hiçbir yerinde kullanılmıyor ve tek
 * bir yerde kalması, kaldırıldığını sanılan bir şeyin tabloda yaşamaya devam
 * etmesi olurdu.
 */
export const BOS = '-'

/**
 * ETKİN YEREL. Ondalık ayracı Türkçe'de virgül, İngilizce'de noktadır.
 *
 * Modül düzeyinde tutuluyor çünkü `sayiBicimle` iki yüzden fazla yerden
 * çağrılıyor ve her birine dil parametresi geçirmek, biçimleme kuralını iki
 * yüz çağrı yerine dağıtmak demekti. TEK YAZAN `DilSaglayici`'dir; başka
 * hiçbir yerden çağrılmaz.
 */
let yerelEtiketi = 'tr-TR'

/**
 * Biçimleyici önbelleği. `Intl.NumberFormat` örneği her çağrıda yeniden
 * kurulmaz: kurulumu biçimlemenin kendisinden pahalıdır ve bu fonksiyon
 * Çizelge ızgarasında satır başına birden çok kez çağrılır.
 *
 * ANAHTAR YERELİ DE İÇERİR. İçermeseydi dil değiştirildiğinde önbellek eski
 * yerelin biçimleyicisini döndürür, sayılar ondalığını virgülle yazmaya
 * devam ederdi.
 */
const ONBELLEK = new Map<string, Intl.NumberFormat>()

function bicimleyici(tur: string, secenekler: Intl.NumberFormatOptions): Intl.NumberFormat {
  const anahtar = `${yerelEtiketi}|${tur}`
  let bulunan = ONBELLEK.get(anahtar)
  if (!bulunan) {
    bulunan = new Intl.NumberFormat(yerelEtiketi, { useGrouping: false, ...secenekler })
    ONBELLEK.set(anahtar, bulunan)
  }
  return bulunan
}

/** Etkin yereli ayarlar. Yalnızca `DilSaglayici` çağırır. */
export function yereliAyarla(dil: Dil): void {
  yerelEtiketi = YEREL[dil]
}

/**
 * Sayıyı ekrana yazılacak biçime çevirir.
 *
 * `ondalik` verilmezse sayı olduğu gibi (gereksiz sıfır eklemeden) yazılır;
 * verilirse `toFixed` gibi tam o basamağa yuvarlanır ve sabitlenir — yan yana
 * dizilen değerlerin aynı basamakta durması sütun hizasının şartıdır.
 */
export function sayiBicimle(deger: number, ondalik?: number): string {
  if (!Number.isFinite(deger)) return BOS
  return ondalik === undefined
    ? bicimleyici('tam', {}).format(deger)
    : bicimleyici(`ondalik${ondalik}`, {
        minimumFractionDigits: ondalik,
        maximumFractionDigits: ondalik,
      }).format(deger)
}

/**
 * İşaretli sapma: `+3,4` · `-1,2` · `0,0`.
 *
 * İşareti `signDisplay: 'exceptZero'` koyar, elle dize birleştirme değil —
 * eksi işaretinin hangi karakter olduğu (ASCII tire mi U+2212 mi) böylece
 * yerelin kararı olur ve iki ayrı yerde iki farklı karaktere ayrışmaz.
 * Sıfır işaretsizdir; "+0" sapma olmadığını değil, ölçülmediğini düşündürür.
 */
export function sapmaBicimle(deger: number, ondalik = 1): string {
  if (!Number.isFinite(deger)) return BOS
  return bicimleyici(`isaretli${ondalik}`, {
    signDisplay: 'exceptZero',
    minimumFractionDigits: ondalik,
    maximumFractionDigits: ondalik,
  }).format(deger)
}
