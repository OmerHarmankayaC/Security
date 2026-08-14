import type { Atama, BlokDegisikligi } from '@/api/types'
import { saatiYaz } from './talepAraligi'
import { gunEkle } from './tarih'

/**
 * Taslak düzenleme oturumu — istemci tarafı (SRS TD-16, FR-6.7, FR-6.8).
 *
 * Düzenleme, sürüme her değişiklikte yazan bir işlem dizisi DEĞİL, kaydedilene
 * kadar biriken bir oturumdur. Değişiklikler burada birikir ve ızgarada anında
 * görünür; sunucuya yazma yalnızca Kaydet ile olur.
 *
 * KURAL DEĞERLENDİRMESİ BURADA YOKTUR ve olmayacaktır. Bu modül yalnızca
 * "hangi blok nerede" sorusunun cevabını taşır; hangi kuralın bozulduğuna
 * sunucu karar verir (FR-6.6). Kuralın istemcide ikinci bir tanımı olsaydı
 * çözücü ile doğrulayıcının aynı tanımdan beslenmesi bozulurdu — bu projede
 * bedeli birkaç kez ödenmiş bir kalıptır.
 *
 * `atamalariUygula` ile sunucudaki `_degisiklikleri_uygula` AYNI veri
 * işlemini yapar (o günün bloğunu yerine koy) ve ikisi de aynı sözleşmeye
 * dayanır: filtre bloğun BAŞLADIĞI güne bakar (SRS TD-1). Bu bir kural değil
 * bir yerleştirme kuralıdır; yine de ayrışabilecekleri için ikisi de test
 * edilmiştir.
 */

export interface Oturum {
  /** Yapılan bütün değişiklikler, sırayla. Geri alınanlar da burada durur. */
  readonly adimlar: readonly BlokDegisikligi[]
  /**
   * Kaç adımın UYGULANDIĞI. Geri al bunu azaltır, yeniden uygula artırır;
   * adımlar silinmediği için yeniden uygulama bilgiyi kaybetmez.
   */
  readonly imlec: number
}

export const BOS_OTURUM: Oturum = { adimlar: [], imlec: 0 }

/** Sunucuya gidecek olan: yalnızca uygulanmış adımlar. */
export function bekleyenler(oturum: Oturum): BlokDegisikligi[] {
  return oturum.adimlar.slice(0, oturum.imlec)
}

export function kirliMi(oturum: Oturum): boolean {
  return oturum.imlec > 0
}

export function geriAlinabilirMi(oturum: Oturum): boolean {
  return oturum.imlec > 0
}

export function yenidenUygulanabilirMi(oturum: Oturum): boolean {
  return oturum.imlec < oturum.adimlar.length
}

/**
 * Yeni bir adım ekler.
 *
 * İMLECİN ÖTESİ ATILIR. Kullanıcı geri alıp sonra başka bir şey yaptığında,
 * geri alınan dal artık erişilemez — tarayıcıların ve metin düzenleyicilerin
 * geri alma yığınıyla aynı davranış. Korunsaydı "yeniden uygula" kullanıcının
 * hiç yapmadığı bir değişikliği geri getirirdi.
 */
export function adimEkle(oturum: Oturum, adim: BlokDegisikligi): Oturum {
  return {
    adimlar: [...oturum.adimlar.slice(0, oturum.imlec), adim],
    imlec: oturum.imlec + 1,
  }
}

export function geriAl(oturum: Oturum): Oturum {
  return geriAlinabilirMi(oturum) ? { ...oturum, imlec: oturum.imlec - 1 } : oturum
}

export function yenidenUygula(oturum: Oturum): Oturum {
  return yenidenUygulanabilirMi(oturum) ? { ...oturum, imlec: oturum.imlec + 1 } : oturum
}

/** Bir blok değişikliği kurar; üçü de boşsa o günün bloğu KALDIRILIR. */
export function blokDegisikligi(
  personelId: number,
  tarih: string,
  aralik: { baslangic: number; bitis: number; noktaId: number } | null,
): BlokDegisikligi {
  if (aralik === null) {
    return {
      personel_id: personelId,
      tarih,
      baslangic_saati: null,
      bitis_saati: null,
      nokta_id: null,
    }
  }
  return {
    personel_id: personelId,
    tarih,
    baslangic_saati: saatiYaz(aralik.baslangic),
    bitis_saati: saatiYaz(aralik.bitis),
    nokta_id: aralik.noktaId,
  }
}

/**
 * Bloğu başka bir personele taşımak İKİ DEĞİŞİKLİKTİR.
 *
 * Kaynaktan kaldırma ve hedefe yazma. Tek bir "taşı" adımı olsaydı sunucunun
 * da onu ayrıca yorumlaması gerekirdi; oysa aynı sonucu iki sıradan adım
 * üretiyor ve geri alma da kendiliğinden doğru çalışıyor — iki adım tek tek
 * geri alınır.
 */
export function tasimaAdimlari(
  kaynakPersonelId: number,
  hedefPersonelId: number,
  tarih: string,
  aralik: { baslangic: number; bitis: number; noktaId: number },
): BlokDegisikligi[] {
  return [
    blokDegisikligi(kaynakPersonelId, tarih, null),
    blokDegisikligi(hedefPersonelId, tarih, aralik),
  ]
}

export function adimlariEkle(oturum: Oturum, adimlar: readonly BlokDegisikligi[]): Oturum {
  return adimlar.reduce(adimEkle, oturum)
}

/**
 * Sürümün atamalarına biriken değişiklikleri uygular — IZGARANIN GÖRDÜĞÜ liste.
 *
 * Her adım o (personel, gün) hücresinin bloğunu yerine koyar: aynı günün
 * bütün blokları önce düşürülür. Filtre bloğun BAŞLADIĞI güne bakar (TD-1) —
 * gece yarısını aşıp bugüne taşan dünkü blok, dünün bloğudur ve el değmeden
 * kalır.
 *
 * Üretilen atamalar NEGATİF kimlik taşır: gerçek bir satır değiller, henüz
 * kaydedilmemiş bir niyetin görüntüsüler. Izgara bunu kilit ve kaynak gibi
 * alanlarda kullanmıyor ama kimliğin çakışmaması React'in liste anahtarı için
 * gerekli.
 */
export function atamalariUygula(
  atamalar: readonly Atama[],
  degisiklikler: readonly BlokDegisikligi[],
): Atama[] {
  let sonuc = [...atamalar]
  let sayac = -1
  for (const d of degisiklikler) {
    sonuc = sonuc.filter((a) => !(a.personel_id === d.personel_id && a.tarih === d.tarih))
    if (d.baslangic_saati === null || d.bitis_saati === null || d.nokta_id === null) continue

    const bas = Number(d.baslangic_saati.slice(0, 2))
    const bitHam = Number(d.bitis_saati.slice(0, 2))
    // Bitiş başlangıçtan küçük ya da eşitse blok gece yarısını aşar —
    // `zaman_araligi` modülündeki sözleşmenin aynısı.
    const sure = ((bitHam - bas + 24) % 24) || 24
    sonuc.push({
      atama_id: sayac,
      personel_id: d.personel_id,
      tarih: d.tarih,
      baslangic_zamani: `${d.tarih}T${d.baslangic_saati}`,
      bitis_zamani: `${gunEkle(d.tarih, bas + sure >= 24 ? 1 : 0)}T${d.bitis_saati}`,
      sure_saat: sure,
      nokta_id: d.nokta_id,
      kilitli: false,
      kaynak: 'manuel',
    })
    sayac -= 1
  }
  return sonuc
}
