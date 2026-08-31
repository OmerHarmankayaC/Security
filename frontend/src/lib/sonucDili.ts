import type { CezaKalemi, DogrulamaSonucu, Ihlal } from '@/api/types'
import { sayiBicimle } from './sayi'
import { buyukHarf } from './metin'
import { etkinDil } from '@/i18n/etkinDil'
import type { Metinler } from '@/i18n/sozluk'

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

export function hedefAdi(kimlik: string, m: Metinler): string {
  return m.sonuc.hedefler[kimlik]?.konu ?? kimlik
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
function miktar(kalem: CezaKalemi, m: Metinler): string {
  const dil = m.sonuc.hedefler[kalem.kural_kimlik]
  const buyukluk = Math.abs(kalem.ham_fark)
  // Ondalık yalnızca gerektiğinde: "1,0 saat" yerine "1 saat".
  const sayi = sayiBicimle(buyukluk, Number.isInteger(buyukluk) ? 0 : 1)
  return dil ? `${sayi} ${dil.birim}` : sayi
}

function konu(kalem: CezaKalemi, m: Metinler): string {
  return m.sonuc.hedefler[kalem.kural_kimlik]?.konu ?? kalem.ad
}

/**
 * Tek bir hedefin cümlesi.
 *
 * Ceza ARTTIĞINDA durum kötüleşmiştir. S1 ve S1f'de bu "açık oluştu" /
 * "açık kapandı" biçiminde okunur; ötekilerde ölçünün adı doğrudan özne
 * olur, çünkü "gece adaleti bozuldu" anlaşılır ama "gece adaleti açıldı"
 * anlamsızdır.
 */
function kalemCumlesi(kalem: CezaKalemi, m: Metinler): string {
  const kotulesti = kalem.ham_fark > 0
  const olcu = miktar(kalem, m)
  if (kalem.kural_kimlik === 'S1') {
    return kotulesti ? m.sonuc.acikArtti(olcu) : m.sonuc.acikAzaldi(olcu)
  }
  if (kalem.kural_kimlik === 'S1f') {
    return kotulesti ? m.sonuc.fazlaAtandi(olcu) : m.sonuc.fazlaAzaldi(olcu)
  }
  const ad = konu(kalem, m)
  return kotulesti ? m.sonuc.bozuldu(ad, olcu) : m.sonuc.iyilesti(ad, olcu)
}

/** Cümlede kaç hedef anılır. Fazlası ayrıntı dökümünün işi. */
const AZAMI_KALEM = 3

export function sonucuOzetle(sonuc: DogrulamaSonucu, m: Metinler): SonucOzeti {
  // ZORUNLU İHLAL VARSA BAŞKA HİÇBİR ŞEY SÖYLENMEZ. Değişiklik
  // uygulanmadığı için ceza dökümü zaten gerçekleşmemiş bir durumu
  // anlatır; onu da göstermek kullanıcıya iki farklı gerçeklik sunardı.
  if (sonuc.zorunlu_ihlaller.length > 0) {
    const kurallar = [...new Set(sonuc.zorunlu_ihlaller.map((i) => i.kural_kimlik))]
    return {
      tur: 'engellendi',
      cumle:
        sonuc.zorunlu_ihlaller.length === 1
          ? m.sonuc.tekIhlal
          : m.sonuc.cokIhlal(sonuc.zorunlu_ihlaller.length, kurallar.join(', ')),
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
      cumle: m.sonuc.etkiYok,
      ihlaller: [],
      uyarilar: sonuc.uyarilar,
      dokum: [],
    }
  }

  const kotulesen = dokum.some((k) => k.ham_fark > 0)
  const iyilesen = dokum.some((k) => k.ham_fark < 0)
  const tur: SonucTuru = kotulesen && iyilesen ? 'karisik' : kotulesen ? 'bozuldu' : 'iyilesti'

  const anilanlar = dokum.slice(0, AZAMI_KALEM).map((k) => kalemCumlesi(k, m))
  const kalan = dokum.length - anilanlar.length
  // Baş harf büyütülür; cümlenin geri kalanı küçük harfle akar.
  const govde = anilanlar.join('; ')
  // Baş harf ETKİN DİLİN yereliyle büyür: Türkçe yereli İngilizce bir
  // cümlenin "i"sini "İ" yapardı.
  const cumle =
    buyukHarf(govde.charAt(0), etkinDil()) +
    govde.slice(1) +
    (kalan > 0 ? m.sonuc.kalanHedef(kalan) : '.')

  return { tur, cumle, ihlaller: [], uyarilar: sonuc.uyarilar, dokum }
}
