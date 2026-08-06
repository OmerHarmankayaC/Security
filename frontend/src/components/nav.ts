export const NAV_OGELERI = [
  'Özet',
  'Tanımlar',
  'Müsaitlik',
  'Tercihler',
  'Çizelge',
  'Çözüm',
  'Analiz',
  'Sürümler',
] as const

export type NavOgesi = (typeof NAV_OGELERI)[number]
