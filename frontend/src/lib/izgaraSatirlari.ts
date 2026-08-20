import type { Atama, Personel } from '@/api/types'

/**
 * Izgarada satırı olacak personel.
 *
 * DÜZENLENEBİLİR SÜRÜMDE KADRO, SALT OKUNURDA ATAMA. Taslak ve çözüldü
 * sürümlerinde soru "kime hâlâ atama yapabilirim" — ataması olmayan da
 * satır olmalı, yoksa boş bir taslakta tıklanacak hücre kalmaz.
 * Yayınlanmış/arşivde soru "ne karar verildi" ve orada boş satır gürültüdür.
 *
 * Aktiflik penceresi süzgeci YALNIZ KADRODAN GELEN satırlara uygulanır:
 * H7 bağlamı o güne atamayı zaten reddediyor (`baglam.musait_mi`) ve satırı
 * göstermek kullanıcıyı asla kabul edilmeyecek bir tıklamaya davet ederdi.
 * Salt okunur sürümde satırlar atamalardan gelir ve süzgeç UYGULANMAZ:
 * orada ataması olan biri, bugün artık aktif olmasa bile satır olmalıdır —
 * geçmişte verilmiş bir karardır ve gizlemek çizelgeyi eksik gösterirdi.
 *
 * Bu, pencerenin ikinci kez okunduğu yerdir; kural değil görünürlük
 * süzgecidir ve ayrışırsa sonucu zararsızdır (sunucu gerekçesiyle reddeder).
 */
export function izgaraSatirlari(girdi: {
  personeller: readonly Personel[]
  atamalar: readonly Atama[]
  duzenlenebilir: boolean
  donemBaslangic: string // ISO
  donemBitis: string // ISO
}): Personel[] {
  const { personeller, atamalar, duzenlenebilir, donemBaslangic, donemBitis } = girdi

  const adaylar = duzenlenebilir
    ? personeller.filter(
        (p) =>
          p.aktif_baslangic <= donemBitis &&
          (p.aktif_bitis === null || p.aktif_bitis >= donemBaslangic),
      )
    : (() => {
        const idler = new Set(atamalar.map((a) => a.personel_id))
        return personeller.filter((p) => idler.has(p.personel_id))
      })()

  return [...adaylar].sort((a, b) => a.ad_soyad.localeCompare(b.ad_soyad, 'tr'))
}
