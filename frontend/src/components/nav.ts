export const NAV_OGELERI = [
  'Özet',
  'Tanımlar',
  'Müsaitlik',
  'Tercihler',
  'Çizelge',
  'Çözüm',
  'Analiz',
  'Sürümler',
  // Yalnız yönetim rolünde menüye girer (bkz. lib/yetki.ts). Listede
  // bulunması bir yetki değildir; kapı sunucudadır (FR-10.4).
  'Kullanıcılar',
] as const

export type NavOgesi = (typeof NAV_OGELERI)[number]

// Tasarım Referansı sürüm 3: yan menü düz bir liste değil, üç başlık
// altında toplanır (bkz. "Sayfa İskeleti — Yan menü").
export interface NavGrubu {
  baslik: string | null
  ogeler: NavOgesi[]
}

export const NAV_GRUPLARI: NavGrubu[] = [
  { baslik: null, ogeler: ['Özet'] },
  { baslik: 'VERİ', ogeler: ['Tanımlar', 'Müsaitlik', 'Tercihler'] },
  { baslik: 'ÜRETİM', ogeler: ['Çizelge', 'Çözüm'] },
  { baslik: 'DEĞERLENDİRME', ogeler: ['Analiz', 'Sürümler'] },
]
