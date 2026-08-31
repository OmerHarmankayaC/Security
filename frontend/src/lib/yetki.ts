import type { Ben, Rol } from '@/api/types'
import type { Metinler } from '@/i18n/sozluk'

/** Hesap uç noktalarına giren roller (SRS 5.10, FR-10.5). */
export const HESAP_YONETEN_ROLLER: readonly Rol[] = ['hesap_yoneticisi', 'sistem_yoneticisi']
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

export type Yuzey = 'giris' | 'parola' | 'calisan' | 'idare'

export function yuzeySec(ben: Ben | null): Yuzey {
  if (ben === null) return 'giris'
  // FR-10.7: parola borcu her şeyin önünde. Sunucu da diğer uç noktaları
  // kapatır; arayüz kullanıcıyı boş ekranlarla baş başa bırakmasın diye
  // doğrudan borcun ödeneceği yere götürür.
  if (ben.parola_degistirmeli) return 'parola'
  return ben.rol === 'calisan' ? 'calisan' : 'idare'
}

/** Sekme başlığı — yüzeyle BİRLİKTE seçilir ki yeni yüzey eklendiğinde
 * başlık eskisinde kalmasın (main.tsx'teki aynı gerekçe). */
export function yuzeyBasligi(yuzey: Yuzey, metin: Metinler): string {
  return metin.sekmeBasligi[yuzey]
}

/** Yönetici arayüzünün menüsü. Kullanıcılar grubu yalnız yönetim rolünde. */
export function navGruplari(rol: Rol): NavGrubu[] {
  // Künye HER ROLE açıktır: projenin ne olduğunu ve kimin geliştirdiğini
  // söyler, veri taşımaz. Menünün en altında, kendi başlığı olmadan durur.
  const kunye: NavGrubu = { baslik: null, ogeler: ['Künye'] }
  // KULLANICILAR EKRANI İDAREYE GÖRÜNMEZ (SRS 5.10). Menüden gizlemek
  // yetkilendirme DEĞİLDİR (FR-10.4) — kapı sunucudadır; buradaki gizleme
  // yalnızca kullanıcıya erişemeyeceği bir yolu göstermemek içindir.
  if (!HESAP_YONETEN_ROLLER.includes(rol)) return [...NAV_GRUPLARI, kunye]
  return [...NAV_GRUPLARI, { baslik: 'yonetim', ogeler: ['Kullanıcılar'] }, kunye]
}
