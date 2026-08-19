import type { CezaKalemi, DogrulamaSonucu, Ihlal } from '@/api/types'
import { sayiBicimle } from './sayi'

/**
 * Doğrulama sonucunun GÜNDELİK DİLE çevrilmesi (SRS FR-6.4, SDD 6.3.3).
 *
 * Ağırlıklı ceza toplamı kullanıcının okumak zorunda olduğu bir sayı değil.
 * Eski ekran "Ceza değişimi: −9999" yazıyordu: yönünü bile söylemiyordu,
 * çünkü işaretin ne anlama geldiği yalnızca modeli bilene açıktı. Üstelik
 * aynı ekranda "Kabul edilebilir" yazısı, kırmızı bir uyarı satırı ve bu
 * sayı üç ayrı yöne bakıyordu.
 *
 * Burada üretilen cümle ÖNCE gelir; sayısal döküm ayrıntı bağlantısının
 * arkasında kalır. Zorunlu ihlal ayrı ve belirgindir — "kabul edilebilir"
 * ile kırmızı uyarı aynı anda GÖRÜNMEZ, çünkü ikisi aynı anda doğru
 * olamaz.
 */

/** Esnek hedefin gündelik dildeki konusu ve ölçü birimi. */
interface HedefDili {
  konu: string
  birim: string
}

/**
 * Kural kimliği → cümlede geçecek konu.
 *
 * Metin kural kataloğundaki `ad` alanından DEĞİL buradan gelir: katalogtaki
 * ad kuralın tanımıdır ("Kişi başına toplam çalışma saatinin adil paydan
 * sapması"), cümlenin öznesi değil. İkisini aynı yerden almak, cümleyi
 * okunmaz bir tanım listesine çevirirdi.
 */
const HEDEF_DILI: Record<string, HedefDili> = {
  S1: { konu: 'kapsama açığı', birim: 'kişi' },
  S1f: { konu: 'talepten fazla kadro', birim: 'kişi' },
  S2: { konu: 'gece adaleti', birim: 'saat' },
  S3: { konu: 'hafta sonu adaleti', birim: 'saat' },
  S4: { konu: 'toplam saat dengesi', birim: 'saat' },
  S5: { konu: 'tercih karşılama', birim: 'tercih' },
  S6: { konu: 'çalışma deseni', birim: 'gün' },
  S6b: { konu: 'bina tutarlılığı', birim: 'gün' },
  S7: { konu: 'izole çalışma günü', birim: 'gün' },
  S8: { konu: 'önceki sürümden sapma', birim: 'atama' },
}

/**
 * Kural kimliğinin ekranda okunacak kısa adı.
 *
 * Çözüm ekranının ceza dökümü yalnız "S1, S1f, S2…" yazıyordu: hangi hedefin
 * ne kadar cezalandığı yalnız kural kataloğunu ezbere bilene açıktı. Adlar
 * BURADAN gelir, katalogtaki `ad` alanından değil — katalog adı kuralın
 * tanımıdır ("Kişi başına toplam çalışma saatinin adil paydan sapması"),
 * bir çubuk grafiğin etiketi değil.
 *
 * Bilinmeyen kimlik kendi kimliğiyle döner: yeni bir kural eklendiğinde
 * ekran boş etiket göstermez, kimliği gösterir.
 */
export function hedefAdi(kimlik: string): string {
  return HEDEF_DILI[kimlik]?.konu ?? kimlik
}

export type SonucTuru = 'engellendi' | 'degisiklik-yok' | 'iyilesti' | 'bozuldu' | 'karisik'

export interface SonucOzeti {
  tur: SonucTuru
  /** Kullanıcının ilk okuyacağı cümle. */
  cumle: string
  /** Zorunlu kısıt ihlalleri — değişiklik UYGULANMAZ. */
  ihlaller: Ihlal[]
  /** Bir yere işaret eden yeni esnek bulgular; engel değil. */
  uyarilar: Ihlal[]
  /** Sayısal döküm — ayrıntı bağlantısının arkasında. */
  dokum: CezaKalemi[]
}

/** "3 saat", "1 kişi". Sayı Mono'da durur; birim düz metindir. */
function miktar(kalem: CezaKalemi): string {
  const dil = HEDEF_DILI[kalem.kural_kimlik]
  const buyukluk = Math.abs(kalem.ham_fark)
  // Ondalık yalnızca gerektiğinde: "1,0 saat" yerine "1 saat".
  const sayi = sayiBicimle(buyukluk, Number.isInteger(buyukluk) ? 0 : 1)
  return dil ? `${sayi} ${dil.birim}` : sayi
}

function konu(kalem: CezaKalemi): string {
  return HEDEF_DILI[kalem.kural_kimlik]?.konu ?? kalem.ad
}

/**
 * Tek bir hedefin cümlesi.
 *
 * Ceza ARTTIĞINDA durum kötüleşmiştir. S1 ve S1f'de bu "açık oluştu" /
 * "açık kapandı" biçiminde okunur; ötekilerde ölçünün adı doğrudan özne
 * olur, çünkü "gece adaleti bozuldu" anlaşılır ama "gece adaleti açıldı"
 * anlamsızdır.
 */
function kalemCumlesi(kalem: CezaKalemi): string {
  const kotulesti = kalem.ham_fark > 0
  if (kalem.kural_kimlik === 'S1') {
    return kotulesti
      ? `kapsama açığı ${miktar(kalem)} arttı`
      : `kapsama açığı ${miktar(kalem)} azaldı`
  }
  if (kalem.kural_kimlik === 'S1f') {
    return kotulesti
      ? `talepten ${miktar(kalem)} fazla atandı`
      : `talepten fazla kadro ${miktar(kalem)} azaldı`
  }
  return `${konu(kalem)} ${miktar(kalem)} ${kotulesti ? 'bozuldu' : 'iyileşti'}`
}

/** Cümlede kaç hedef anılır. Fazlası ayrıntı dökümünün işi. */
const AZAMI_KALEM = 3

export function sonucuOzetle(sonuc: DogrulamaSonucu): SonucOzeti {
  // ZORUNLU İHLAL VARSA BAŞKA HİÇBİR ŞEY SÖYLENMEZ. Değişiklik
  // uygulanmadığı için ceza dökümü zaten gerçekleşmemiş bir durumu
  // anlatır; onu da göstermek kullanıcıya iki farklı gerçeklik sunardı.
  if (sonuc.zorunlu_ihlaller.length > 0) {
    const kurallar = [...new Set(sonuc.zorunlu_ihlaller.map((i) => i.kural_kimlik))]
    return {
      tur: 'engellendi',
      cumle:
        sonuc.zorunlu_ihlaller.length === 1
          ? 'Bu değişiklik bir zorunlu kuralı bozuyor ve uygulanmadı.'
          : `Bu değişiklik ${sonuc.zorunlu_ihlaller.length} zorunlu kuralı bozuyor ve uygulanmadı (${kurallar.join(', ')}).`,
      ihlaller: sonuc.zorunlu_ihlaller,
      uyarilar: [],
      dokum: [],
    }
  }

  const dokum = [...sonuc.ceza_dokumu]
    .filter((k) => k.ham_fark !== 0)
    .sort((a, b) => Math.abs(b.agirlikli_fark) - Math.abs(a.agirlikli_fark))

  if (dokum.length === 0) {
    return {
      tur: 'degisiklik-yok',
      cumle: 'Değişiklik hiçbir hedefi etkilemedi.',
      ihlaller: [],
      uyarilar: sonuc.uyarilar,
      dokum: [],
    }
  }

  const kotulesen = dokum.some((k) => k.ham_fark > 0)
  const iyilesen = dokum.some((k) => k.ham_fark < 0)
  const tur: SonucTuru = kotulesen && iyilesen ? 'karisik' : kotulesen ? 'bozuldu' : 'iyilesti'

  const anilanlar = dokum.slice(0, AZAMI_KALEM).map(kalemCumlesi)
  const kalan = dokum.length - anilanlar.length
  // Baş harf büyütülür; cümlenin geri kalanı küçük harfle akar.
  const govde = anilanlar.join('; ')
  const cumle =
    govde.charAt(0).toLocaleUpperCase('tr-TR') +
    govde.slice(1) +
    (kalan > 0 ? ` ve ${kalan} hedef daha etkilendi.` : '.')

  return { tur, cumle, ihlaller: [], uyarilar: sonuc.uyarilar, dokum }
}
