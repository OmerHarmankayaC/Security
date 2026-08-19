import type { KisiSayisi } from '@/api/types'

export interface AdaletSatiri {
  personel_id: number
  ad_soyad: string
  /** Ölçülen saat. */
  saat: number
  /** Kişiye düşen adil pay — referans (SRS S2/S3). */
  pay: number
  /** Çözücünün cezalandırdığı sapma; taban/tavan yöntemiyle ve İŞARETSİZ. */
  sapma: number
  /**
   * Yükün adil paya göre yönü. Sapmanın BÜYÜKLÜĞÜNDEN AYRI TÜRETİLİR:
   * büyüklük çözücünün taban/tavan formülüdür, yön ise yükün payla
   * doğrudan kıyası. Kesirli payda ikisi ayrışır — pay 7,4 iken 7 saat
   * çalışan kişinin çözücü ölçüsü 1'dir ama kişi payının ALTINDADIR.
   *
   * `yok`: taban/tavan bandının içinde, cezasız — çubuk hiç çizilmez.
   */
  yon: 'ust' | 'alt' | 'yok'
}

/**
 * Bir adalet ölçüsünün satırları, sapması büyükten küçüğe.
 *
 * SAPMA ÇÖZÜCÜNÜN KENDİ FORMÜLÜDÜR: `max(saat − ⌊pay⌋, ⌈pay⌉ − saat, 0)`
 * (SRS S2/S3, `kurallar/esnek.py:_adalet_sapmasi_ihlalleri`). Ekranda daha
 * hoş duran bir ölçü (örneğin işaretli `saat − pay`) kullanmak, aynı çizelge
 * için ceza dökümünde başka, adalet grafiğinde başka bir sayı gösterirdi;
 * bu projede aynı bilginin iki türetme yolu bulunması tekrarlayan bir hata.
 *
 * Sayı işaretsizdir — yön, çubuğun referans çizgisine göre nerede durduğundan
 * okunur.
 */
export function adaletSatirlari(kalemler: readonly KisiSayisi[]): AdaletSatiri[] {
  return kalemler
    .map((k) => {
      const pay = k.pay ?? 0
      const sapma = Math.max(k.sayi - Math.floor(pay), Math.ceil(pay) - k.sayi, 0)
      const yon: AdaletSatiri['yon'] = sapma === 0 ? 'yok' : k.sayi > pay ? 'ust' : 'alt'
      return { personel_id: k.personel_id, ad_soyad: k.ad_soyad, saat: k.sayi, pay, sapma, yon }
    })
    .sort((a, b) => b.sapma - a.sapma || b.saat - a.saat)
}
