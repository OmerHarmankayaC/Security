import type { Kural } from '@/api/types'

/**
 * Izgaranın sürükleme sınırlarını kural kataloğundan okur (Tur 6 İş 4).
 *
 * DEĞER KODA GÖMÜLMEZ. Asgari blok süresi ve günlük azami saat kullanıcının
 * değiştirebildiği kural parametreleridir (SRS 3.3.5, H1 ve H9); ekrana sabit
 * yazılsalardı kullanıcı parametreyi değiştirdiğinde sürükleme eski sınırı
 * göstermeye devam eder ve kullanıcı sunucudan gelen reddi anlayamazdı. Bu
 * proje aynı kalıptan daha önce zarar gördü: aynı sayının iki yerde durması.
 *
 * PASİF KURAL SINIR KOYMAZ. Kural pasifleştirilmişse çözücü ve doğrulayıcı o
 * sınırı uygulamaz; ızgaranın uygulaması kullanıcıyı sunucunun kabul edeceği
 * bir seçimden alıkoyardı.
 */
export interface BlokSinirlari {
  /** H1'in asgari blok süresi; kural pasifse `null`. */
  asgariSaat: number | null
  /** H9'un günlük azami saati; kural pasifse `null`. */
  azamiSaat: number | null
}

function etkinParametre(
  kurallar: readonly Kural[],
  kimlik: string,
  anahtar: string,
): number | null {
  const kural = kurallar.find((k) => k.kimlik === kimlik)
  if (!kural || !kural.aktif) return null
  const deger = kural.parametreler[anahtar]
  return typeof deger === 'number' && Number.isFinite(deger) ? deger : null
}

export function blokSinirlariniOku(kurallar: readonly Kural[]): BlokSinirlari {
  return {
    asgariSaat: etkinParametre(kurallar, 'H1', 'asgari_blok_saat'),
    azamiSaat: etkinParametre(kurallar, 'H9', 'azami_gunluk_saat'),
  }
}

/**
 * Sürüklenen aralık sınırların dışındaysa NEDENİNİ söyleyen cümle; içindeyse
 * `null`.
 *
 * Sınır sürükleme SIRASINDA görünsün diye ayrı bir fonksiyon: kullanıcı
 * geçersiz bir seçimi tamamlayıp sonra reddedilmek yerine sınırı elinde
 * hissetmeli (Tur 6 İş 4). Metin sunucunun ihlal mesajını taklit etmez, onu
 * ÖNCELER.
 */
export function sinirUyarisi(sureSaat: number, sinirlar: BlokSinirlari): string | null {
  if (sinirlar.asgariSaat !== null && sureSaat < sinirlar.asgariSaat) {
    return `Asgari blok ${sinirlar.asgariSaat} saat (H1)`
  }
  if (sinirlar.azamiSaat !== null && sureSaat > sinirlar.azamiSaat) {
    return `Günlük azami ${sinirlar.azamiSaat} saat (H9)`
  }
  return null
}
