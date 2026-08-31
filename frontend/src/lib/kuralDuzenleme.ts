import { BOS } from './sayi'
import type { Kural } from '@/api/types'

/**
 * Kural düzenleme kipinin değişiklik hesabı (madde 3a).
 *
 * Kip neden var: aktif/pasif rozetine tek tık kuralı anında ve geri dönüşsüz
 * değiştiriyordu. Yanlış bir tık sessizce kalıcı oluyordu — canlıda S1'in
 * pasif çıkması tam olarak bu yolla oldu. Artık değişiklikler yerel bir
 * taslakta birikir, kullanıcı ne kaydedeceğini görerek onaylar.
 */

/** Kaydedilecek tek bir alan değişikliği; onay metni bundan kurulur. */
export interface KuralDegisikligi {
  kimlik: string
  ad: string
  /**
   * Değişen alanın KİMLİĞİ, görünen adı değil.
   *
   * `'aktiflik'` ve `'agirlik'` sabit alanlar; başka her değer bir parametre
   * anahtarıdır ve zaten kullanıcının girdiği ada karşılık gelir. Görünen
   * metni ekran sözlükten yazar.
   *
   * Kimlik olmasının pratik bir sonucu da var: bu fonksiyon SAF kalıyor ve
   * `kirliMi` gibi yalnızca "değişiklik var mı" diye soran çağrılar sözlük
   * taşımak zorunda kalmıyor.
   */
  alan: 'aktiflik' | 'agirlik' | (string & {})
  onceki: string
  yeni: string
}

/** Bir kural için sunucuya gidecek gövde. */
export interface KuralYazma {
  kimlik: string
  govde: Partial<Pick<Kural, 'aktif' | 'agirlik' | 'parametreler'>>
}

// Aktif/pasif DEĞERİ de bir kimliktir; ekran onu sözlükten yazar.
function aktiflikMetni(aktif: boolean): string {
  return aktif ? 'aktif' : 'pasif'
}

function sayiMetni(deger: unknown): string {
  return deger === null || deger === undefined ? BOS : String(deger)
}

/**
 * Taslak ile özgün kural listesi arasındaki farkları kullanıcı diliyle döndürür.
 *
 * Yalnızca GERÇEKTEN değişen alanlar listelenir; kullanıcı bir alana girip
 * aynı değeri bıraktığında onay kutusunda "değişiklik" görünmemeli, yoksa
 * onayın kendisi güvenilirliğini kaybeder.
 */
export function degisiklikleriBul(orijinal: Kural[], taslak: Kural[]): KuralDegisikligi[] {
  const oncekiler = new Map(orijinal.map((k) => [k.kimlik, k]))
  const degisiklikler: KuralDegisikligi[] = []

  for (const yeni of taslak) {
    const eski = oncekiler.get(yeni.kimlik)
    if (!eski) continue

    if (eski.aktif !== yeni.aktif) {
      degisiklikler.push({
        kimlik: yeni.kimlik,
        ad: yeni.ad,
        alan: 'aktiflik',
        onceki: aktiflikMetni(eski.aktif),
        yeni: aktiflikMetni(yeni.aktif),
      })
    }

    if (eski.agirlik !== yeni.agirlik) {
      degisiklikler.push({
        kimlik: yeni.kimlik,
        ad: yeni.ad,
        alan: 'agirlik',
        onceki: sayiMetni(eski.agirlik),
        yeni: sayiMetni(yeni.agirlik),
      })
    }

    for (const tanim of yeni.parametre_tanimlari) {
      const oncekiDeger = eski.parametreler[tanim.anahtar]
      const yeniDeger = yeni.parametreler[tanim.anahtar]
      if (oncekiDeger !== yeniDeger) {
        degisiklikler.push({
          kimlik: yeni.kimlik,
          ad: yeni.ad,
          alan: tanim.etiket,
          onceki: sayiMetni(oncekiDeger),
          yeni: sayiMetni(yeniDeger),
        })
      }
    }
  }

  return degisiklikler
}

/**
 * Sunucuya gidecek istekler: kural başına TEK istek, yalnızca değişen alanlarla.
 *
 * Alan başına istek atmak, kısmi kaydedilmiş bir kural (ağırlık gitti,
 * aktiflik gitmedi) bırakabilirdi; kural başına toplamak bunu engeller.
 * Değişmeyen alan gövdeye hiç konmaz — backend `exclude_unset` ile çalışır,
 * gönderilmeyen alan yazılmaz.
 */
export function yazilacaklariBul(orijinal: Kural[], taslak: Kural[]): KuralYazma[] {
  const oncekiler = new Map(orijinal.map((k) => [k.kimlik, k]))
  const yazmalar: KuralYazma[] = []

  for (const yeni of taslak) {
    const eski = oncekiler.get(yeni.kimlik)
    if (!eski) continue
    const govde: KuralYazma['govde'] = {}

    if (eski.aktif !== yeni.aktif) govde.aktif = yeni.aktif
    if (eski.agirlik !== yeni.agirlik) govde.agirlik = yeni.agirlik

    const degisenParametreler: Record<string, unknown> = {}
    for (const tanim of yeni.parametre_tanimlari) {
      if (eski.parametreler[tanim.anahtar] !== yeni.parametreler[tanim.anahtar]) {
        degisenParametreler[tanim.anahtar] = yeni.parametreler[tanim.anahtar]
      }
    }
    if (Object.keys(degisenParametreler).length > 0) govde.parametreler = degisenParametreler

    if (Object.keys(govde).length > 0) yazmalar.push({ kimlik: yeni.kimlik, govde })
  }

  return yazmalar
}

/** Taslakta kaydedilmemiş değişiklik var mı? */
export function kirliMi(orijinal: Kural[], taslak: Kural[]): boolean {
  return degisiklikleriBul(orijinal, taslak).length > 0
}
