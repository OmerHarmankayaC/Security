import {
  Calendar,
  ChartColumn,
  Database,
  Grid3x3,
  House,
  Layers,
  Play,
  Star,
  Info,
  Users,
  type LucideIcon,
} from 'lucide-react'

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
  'Künye',
] as const

export type NavOgesi = (typeof NAV_OGELERI)[number]

/**
 * Menü simgeleri (Tasarım Referansı sürüm 4, "Menü simgeleri").
 *
 * Kural: 17×17px, kontur kalınlığı 2, dolgu yok, sade geometri. Renk metinle
 * aynıdır — ayrı bir renk sınıfı verilmez, `currentColor` üzerinden menü
 * öğesinin kendi renginden (aktif `chrome-ink`, pasif `chrome-ink-muted`)
 * miras alınır.
 *
 * Kaynak lucide-react: projede zaten bağımlılıktı ve kontur tabanlı olduğu
 * için kuralın üçüne birden uyuyor; inline SVG yazmak yerine o kullanılır,
 * yeni bağımlılık eklenmez.
 *
 * `Kullanıcılar` dokümandaki sekiz öğenin dışındadır (kimlik doğrulama
 * fazında eklendi, Figma'da karşılığı henüz yok — bkz. TASARIM_REFERANSI.md
 * "Henüz tasarlanmamış"). Menüde simgesiz tek öğe kalmasın diye eşlendi.
 */
export const NAV_SIMGELERI: Record<NavOgesi, LucideIcon> = {
  Özet: House,
  Tanımlar: Database,
  Müsaitlik: Calendar,
  Tercihler: Star,
  Çizelge: Grid3x3,
  Çözüm: Play,
  Analiz: ChartColumn,
  Sürümler: Layers,
  Kullanıcılar: Users,
  Künye: Info,
}

// Tasarım Referansı sürüm 4: yan menü düz bir liste değil, üç başlık
// altında toplanır (bkz. "Sayfa İskeleti, Yan menü").
//
// Başlık bir KİMLİK, görünen metin değil: menü iki dilli ve başlığın
// kendisi burada yazılı olsaydı çeviri bileşenin içinde bir tabloya
// bakmak zorunda kalırdı. Görünen ad sözlükte (`menuGruplari`).
export type NavGrubuAdi = 'veri' | 'uretim' | 'degerlendirme' | 'yonetim'

export interface NavGrubu {
  baslik: NavGrubuAdi | null
  ogeler: NavOgesi[]
}

export const NAV_GRUPLARI: NavGrubu[] = [
  { baslik: null, ogeler: ['Özet'] },
  { baslik: 'veri', ogeler: ['Tanımlar', 'Müsaitlik', 'Tercihler'] },
  { baslik: 'uretim', ogeler: ['Çizelge', 'Çözüm'] },
  { baslik: 'degerlendirme', ogeler: ['Analiz', 'Sürümler'] },
]
