import type { Ben, Rol } from '@/api/types'
import { NAV_GRUPLARI, type NavGrubu } from '@/components/nav'

/**
 * Giriş yapan kullanıcının açılacağı yüzey ve göreceği menü (SRS 5.10).
 *
 * Saf fonksiyonlar hâlinde ayrı durmalarının nedeni testlenebilirlik değil
 * yalnızca: bu kararlar bileşenlerin içine dağılsaydı, "yönetici Kullanıcılar
 * ekranını görüyor mu" sorusunun yanıtı üç dosyada birden aranırdı.
 *
 * BURADAKİ HİÇBİR ŞEY YETKİLENDİRME DEĞİLDİR. Menüden bir öğeyi çıkarmak
 * ya da bir yüzeyi göstermemek, o uç noktayı kapatmaz; kapı sunucudadır
 * (SRS FR-10.4, backend/app/guvenlik.py). Buradaki seçim yalnızca
 * kullanıcıya erişemeyeceği bir şeyi göstermemek içindir.
 */

export type Yuzey = 'giris' | 'parola' | 'calisan' | 'yonetici'

export function yuzeySec(ben: Ben | null): Yuzey {
  if (ben === null) return 'giris'
  // FR-10.7: parola borcu her şeyin önünde. Sunucu da diğer uç noktaları
  // kapatır; arayüz kullanıcıyı boş ekranlarla baş başa bırakmasın diye
  // doğrudan borcun ödeneceği yere götürür.
  if (ben.parola_degistirmeli) return 'parola'
  return ben.rol === 'calisan' ? 'calisan' : 'yonetici'
}

/** Sekme başlığı — yüzeyle BİRLİKTE seçilir ki yeni yüzey eklendiğinde
 * başlık eskisinde kalmasın (main.tsx'teki aynı gerekçe). */
export function yuzeyBasligi(yuzey: Yuzey): string {
  switch (yuzey) {
    case 'giris':
      return 'Vardiya — Giriş'
    case 'parola':
      return 'Vardiya — Parola'
    case 'calisan':
      return 'Vardiya — Çalışan'
    case 'yonetici':
      return 'Vardiya — Admin'
  }
}

/** Yönetici arayüzünün menüsü. Kullanıcılar grubu yalnız yönetim rolünde. */
export function navGruplari(rol: Rol): NavGrubu[] {
  // Künye HER ROLE açıktır: projenin ne olduğunu ve kimin geliştirdiğini
  // söyler, veri taşımaz. Menünün en altında, kendi başlığı olmadan durur.
  const kunye: NavGrubu = { baslik: null, ogeler: ['Künye'] }
  if (rol !== 'yonetim') return [...NAV_GRUPLARI, kunye]
  return [...NAV_GRUPLARI, { baslik: 'YÖNETİM', ogeler: ['Kullanıcılar'] }, kunye]
}
