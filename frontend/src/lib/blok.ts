import type { Metinler } from '@/i18n/sozluk'
/**
 * Çalışma bloğunun okunması — TEK YER (SRS TD-13, SDD 4.2.1).
 *
 * Atama artık bir vardiya tipi taşımıyor; iki zaman damgası taşıyor
 * (`baslangic_zamani`, `bitis_zamani`). Ekranların hepsi aynı üç soruyu
 * soruyor — "kaçta başladı", "kaçta bitti", "ne kadar gece" — ve üçünün de
 * yanıtı burada. Kopyalandığında ayrışacak yer gün sınırıdır: gece yarısını
 * aşan blokta bitiş ertesi güne düşer ve `24` yazılması gerekir.
 *
 * Zaman damgaları sunucudan saat dilimi ofsetiyle gelir. Saat, dizeden
 * DOĞRUDAN okunur; `new Date(...)` kullanılsaydı tarayıcının yerel saat
 * dilimi devreye girer ve aynı çizelge iki makinede farklı saatlerde
 * görünürdü.
 */

import { gunEkle } from './tarih'

/** "2026-02-02T08:00:00+03:00" → 8. */
export function baslangicSaati(zaman: string): number {
  return Number(zaman.slice(11, 13))
}

/** Bitiş saati; gün sonu `24` yazılır (00.00 bir aralığı sıfır uzunlukta gösterir). */
export function bitisSaati(zaman: string): number {
  const saat = Number(zaman.slice(11, 13))
  return saat === 0 ? 24 : saat
}

/** 8 → "08.00". Ondalık ayraç NOKTA (Tasarım Referansı). */
export function saatEtiketi(saat: number): string {
  return `${String(saat).padStart(2, '0')}.00`
}

/** Bloğun ekrandaki hâli: "08.00–16.00". */
export function blokEtiketi(baslangic: string, bitis: string): string {
  return `${saatEtiketi(baslangicSaati(baslangic))}–${saatEtiketi(bitisSaati(bitis))}`
}

/**
 * İki zaman damgasından bloğun saat cinsinden süresi.
 *
 * Sunucu `sure_saat`i zaten türetip gönderiyor ve okuma yüzeylerinin çoğu onu
 * kullanır; bu yardımcı, süreyi taşımayan kayıtlar içindir (çalışan panelinin
 * "kaldırılan gün" satırı yalnızca iki damga tutar). Fark sıfırsa blok gün
 * boyudur — `talepAraligi.araligiSure` ile AYNI kural.
 */
export function blokSuresi(baslangic: string, bitis: string): number {
  const fark = (bitisSaati(bitis) - baslangicSaati(baslangic) + 24) % 24
  return fark === 0 ? 24 : fark
}

/** Izgara hücresinin kısa hâli: "08–16". */
export function blokKisaEtiketi(baslangic: string, bitis: string): string {
  const bas = String(baslangicSaati(baslangic)).padStart(2, '0')
  const bit = String(bitisSaati(bitis)).padStart(2, '0')
  return `${bas}–${bit}`
}

/**
 * Bloğun BİR GÜN ızgarasındaki parçası (SDD 6.3.3, İş 1).
 *
 * Gün ızgarasının tek geometri kaynağı. Gece yarısını aşan blok iki günün
 * ızgarasında da görünür ama **tek bloktur** (SRS TD-13): başladığı günde sağ
 * kenara dayanır, ertesi gün sol kenardan başlar. İki bayrak bunu söyler;
 * ekran onlara bakarak kenarı açık çizer. İkinci bir çözümleme yazılırsa
 * ayrışacak yer tam olarak burasıdır — 24'ün mod'u iki yerde farklı yazılır.
 */
export interface GunParcasi {
  /** Parçanın o gün içindeki başlangıcı, 0–23. */
  baslangic: number
  /** Parçanın o gün içindeki bitişi, 1–24. */
  bitis: number
  /** Parça önceki günde başlamış bir bloğun devamı. */
  oncekiGundenGeliyor: boolean
  /** Blok bu günün sonunda bitmiyor, ertesi güne taşıyor. */
  sonrakiGuneTasiyor: boolean
}

/** `gunParcasi`nın okuduğu asgari blok şekli — `Atama`nın alt kümesi. */
export interface BlokGibi {
  /** Bloğun SAYILDIĞI gün (SRS TD-1); duvar saati günü değil. */
  tarih: string
  baslangic_zamani: string
  sure_saat: number
}

/**
 * Bloğun `gun` ızgarasındaki parçası; blok o güne hiç değmiyorsa `null`.
 *
 * Blok başladığı güne sayılır (TD-1), bu yüzden `tarih` başlangıç günüdür ve
 * kıyas ondan yapılır. Süre 24'ü aştığında (kural olarak aşamaz — H9 günlük
 * tavanı on bir saattir) parça yine gün sınırında kesilir.
 */
export function gunParcasi(blok: BlokGibi, gun: string): GunParcasi | null {
  const bas = baslangicSaati(blok.baslangic_zamani)
  const ham = bas + blok.sure_saat

  if (gun === blok.tarih) {
    return {
      baslangic: bas,
      bitis: Math.min(24, ham),
      oncekiGundenGeliyor: false,
      sonrakiGuneTasiyor: ham > 24,
    }
  }

  if (ham > 24 && gun === gunEkle(blok.tarih, 1)) {
    return {
      baslangic: 0,
      bitis: Math.min(24, ham - 24),
      oncekiGundenGeliyor: true,
      sonrakiGuneTasiyor: ham - 24 > 24,
    }
  }

  return null
}

/**
 * Bir günün ızgarasında görünen parçalar: o gün başlayan blok ve önceki
 * günden taşan blok. H1 günde tek başlangıç şart koştuğu için liste en çok
 * iki eleman taşır ve ikisi FARKLI bloklardır.
 */
export function gununParcalari<T extends BlokGibi>(
  bloklar: readonly T[],
  gun: string,
): { blok: T; parca: GunParcasi }[] {
  const parcalar: { blok: T; parca: GunParcasi }[] = []
  for (const blok of bloklar) {
    const parca = gunParcasi(blok, gun)
    if (parca) parcalar.push({ blok, parca })
  }
  return parcalar.sort((a, b) => a.parca.baslangic - b.parca.baslangic)
}

/**
 * Bloğun ızgaradaki erişilebilir etiketi.
 *
 * RENK TEK BAŞINA BİLGİ TAŞIMAZ (SDD 6.3.3, İş 3): renk körlüğü ve siyah-beyaz
 * yazdırma nedeniyle saat aralığı metin olarak da bulunmak zorundadır. Gece
 * yarısını aşan blokta aralık BLOĞUN TAMAMINI söyler, o günkü parçasını değil —
 * "20.00–24.00" iki ayrı blok izlenimi verirdi ve modelin yasakladığı şey tam
 * olarak budur (SRS TD-13).
 */
export function blokErisilebilirEtiket(
  blok: BlokGibi & { bitis_zamani: string },
  parca: GunParcasi,
  noktaAdi: string,
  m: Metinler,
): string {
  const aralik = blokEtiketi(blok.baslangic_zamani, blok.bitis_zamani)
  const govde = `${aralik} · ${noktaAdi}`
  if (parca.oncekiGundenGeliyor) return `${govde} · ${m.izgara.oncekiGundenDevam}`
  if (parca.sonrakiGuneTasiyor) return `${govde} · ${m.izgara.ertesiGuneTasiyor}`
  return govde
}

// Gece dönemi (SRS TD-2): 20:00–06:00. Yarı açık aralık — 06 gece değildir.
const GECE_BASLANGIC = 20
const GECE_BITIS = 6

/**
 * Bloğun gece dönemiyle kesişiminin uzunluğu (SRS TD-2).
 *
 * GECE HESAPLANIR, İŞARETLENMEZ. Önceki sürümlerde vardiya tipi üzerinde bir
 * `gece_mi` bayrağı vardı; blok kataloğu kalktığı için işaretlenecek bir
 * nesne de kalmadı. Sunucudaki `gece_saat_sayisi` ile aynı hesap.
 */
export function geceSaati(baslangic: string, sureSaat: number): number {
  let sayac = 0
  for (let kayma = 0; kayma < sureSaat; kayma += 1) {
    const saat = (baslangicSaati(baslangic) + kayma) % 24
    if (saat >= GECE_BASLANGIC || saat < GECE_BITIS) sayac += 1
  }
  return sayac
}


/**
 * Sapma kaydının (kapsama açığı / fazla kadro) okunması — TEK YER.
 *
 * Kayıt artık tarih + ofsetsiz saat değil ZAMAN DAMGASI taşıyor (B-23);
 * aralık gün sınırını kendisi taşır. Kaydın sayıldığı gün başlangıç
 * damgasından türetilir — aynı sözleşme atamada da geçerli (SRS TD-1).
 */
export interface SapmaAraligi {
  baslangic_zamani: string
  bitis_zamani: string
}

/** Sapmanın sayıldığı gün: başlangıç damgasının tarihi. */
export function sapmaGunu(sapma: SapmaAraligi): string {
  return sapma.baslangic_zamani.slice(0, 10)
}

/** Sapmanın ekrandaki aralığı: "22.00–02.00". */
export function sapmaEtiketi(sapma: SapmaAraligi): string {
  return blokEtiketi(sapma.baslangic_zamani, sapma.bitis_zamani)
}

/** Sapmanın saat cinsinden uzunluğu; gün sınırını aşan aralıkta da doğru. */
export function sapmaSuresi(sapma: SapmaAraligi): number {
  return blokSuresi(sapma.baslangic_zamani, sapma.bitis_zamani)
}
