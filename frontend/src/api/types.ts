// Backend semalarinin (app/schemas/*.py) TypeScript karsiliklari.
// Yalnizca Cizelge/Cozum ekranlarinin (Sprint 2 Gun 10) kullandigi alanlar.

export interface Donem {
  donem_id: number
  baslangic_tarihi: string
  bitis_tarihi: string
  tercih_son_tarihi: string
}

export type CizelgeSurumuDurumu = 'taslak' | 'cozuldu' | 'yayinlandi' | 'arsiv'

export interface CizelgeSurumu {
  surum_id: number
  donem_id: number
  surum_no: number
  durum: CizelgeSurumuDurumu
  onceki_surum_id: number | null
  yayin_zamani: string | null
  guncelleme_zamani: string
}

export type AtamaKaynagi = 'cozucu' | 'manuel'

export interface Atama {
  atama_id: number
  personel_id: number
  tarih: string
  vardiya_tipi_id: number
  nokta_id: number
  kilitli: boolean
  kaynak: AtamaKaynagi
}

export interface KapsamaAcigi {
  acik_id: number
  tarih: string
  vardiya_tipi_id: number
  nokta_id: number
  eksik_sayi: number
}

export interface Personel {
  personel_id: number
  ad_soyad: string
  sicil_no: string
  haftalik_hedef_saat: number
  sabit_vardiya_tipi_id: number | null
  aktif_baslangic: string
  aktif_bitis: string | null
  yetkinlik_idleri: number[]
}

export interface VardiyaTipi {
  vardiya_tipi_id: number
  ad: string
  baslangic_saati: string
  bitis_saati: string
  sure_saat: string
  gece_mi: boolean
}

export interface GorevNoktasi {
  nokta_id: number
  ad: string
  bina_id: number | null
  onkosul_yetkinlik_id: number | null
  aktif: boolean
}

export type CozumIsiDurumu =
  | 'kuyrukta'
  | 'on_kontrol'
  | 'cozuluyor'
  | 'tamamlandi'
  | 'uyarili'
  | 'basarisiz'
  | 'iptal'

export interface CozumIsi {
  is_id: number
  surum_id: number
  durum: CozumIsiDurumu
  baslangic_zamani: string
  bitis_zamani: string | null
  sure_saniye: string | null
  zaman_limiti_saniye: number
  en_iyi_ceza: string | null
  ceza_dokumu: Record<string, number> | null
  hata_mesaji: string | null
}

export type OnKontrolBulguTipi =
  | 'donem_kapasitesi'
  | 'yetkinlik_havuzu'
  | 'gunluk_musaitlik'
  | 'nokta_musaitlik'

export interface OnKontrolBulgu {
  tip: OnKontrolBulguTipi
  aciklama: string
  eksik: number | null
  yetkinlik_id: number | null
  tarih: string | null
  vardiya_tipi_id: number | null
  nokta_id: number | null
}

export interface Ihlal {
  kural_kimlik: string
  aciklama: string
  personel_id: number | null
  tarih: string | null
  ceza: number | null
}

export interface DogrulamaSonucu {
  kabul_edilebilir: boolean
  zorunlu_ihlaller: Ihlal[]
  ceza_degisimi: number
}

export interface AtamaDegisikligiIstek {
  surum_id: number
  personel_id: number
  tarih: string
  vardiya_tipi_id: number | null
  nokta_id: number | null
}

// --- Tanımlar (Sprint 3 Ara İş) --------------------------------------------

export interface Yetkinlik {
  yetkinlik_id: number
  ad: string
  aciklama: string | null
}

export interface Bina {
  bina_id: number
  ad: string
}

export type GunTipi = 'hafta_ici' | 'hafta_sonu' | 'resmi_tatil'

export interface TalepHucresi {
  talep_id: number
  nokta_id: number
  vardiya_tipi_id: number
  gun_tipi: GunTipi
  tarih: string | null
  gereken_sayi: number
}

export interface YukGostergesi {
  haftalik_kisi_vardiya: number
  haftalik_kisi_saat: string
  asgari_kadro: number
}

export interface TalepYaniti {
  hucreler: TalepHucresi[]
  yuk_gostergesi: YukGostergesi
}

export type KuralTipi = 'zorunlu' | 'esnek'

export interface Kural {
  kural_id: number
  kimlik: string
  tip: KuralTipi
  parametreler: Record<string, unknown>
  agirlik: number | null
  aktif: boolean
}

// --- Müsaitlik (FR-2.x) ----------------------------------------------------

export type MusaitlikDilimi = 'tam_gun' | 'ogleden_once' | 'ogleden_sonra'
export type MusaitlikTipi = 'yillik_izin' | 'rapor' | 'egitim' | 'mazeret'

export interface Musaitlik {
  musaitlik_id: number
  personel_id: number
  baslangic_tarihi: string
  bitis_tarihi: string
  dilim: MusaitlikDilimi
  tip: MusaitlikTipi
  not_: string | null
}

export interface MusaitlikOlusturIstek {
  personel_id: number
  baslangic_tarihi: string
  bitis_tarihi: string
  dilim: MusaitlikDilimi
  tip: MusaitlikTipi
  not_?: string | null
}

// --- Tercih (FR-3.x) --------------------------------------------------------

export type TercihTipi = 'calismama' | 'vardiya_tipi_tercihi'
export type TercihDurumu = 'beklemede' | 'onaylandi' | 'reddedildi'

export interface Tercih {
  tercih_id: number
  personel_id: number
  donem_id: number
  tarih: string
  tip: TercihTipi
  vardiya_tipi_id: number | null
  durum: TercihDurumu
  calisan_notu: string | null
  ret_gerekcesi: string | null
}

// --- Analiz (FR-8.x, SDD 5.7) -----------------------------------------------

export interface KisiSayisi {
  personel_id: number
  ad_soyad: string
  sayi: number
}

export interface SaatDengesi {
  personel_id: number
  ad_soyad: string
  toplam_saat: number
  hedef_saat: number
  sapma: number
}

export interface Analiz {
  surum_id: number
  kapsama_orani: number
  kisi_basina_gece: KisiSayisi[]
  kisi_basina_hafta_sonu: KisiSayisi[]
  saat_dagilimi: SaatDengesi[]
  en_dengesiz_personel_id: number | null
  en_dengesiz_ad_soyad: string | null
  tercih_karsilama_orani: number | null
  bina_degisim_sayisi: KisiSayisi[]
  ceza_dokumu: Record<string, number> | null
  toplam_ceza: number | null
}

// --- Çalışan Paneli (SDD 6.1, Ek B; SRS FR-9.x) -----------------------------

export type DegisimTipi = 'eklendi' | 'degisti'
export type KarsilanmaDurumu = 'karsilandi' | 'karsilanmadi' | 'henuz_belirsiz'

export interface Vardiyam {
  tarih: string
  vardiya_tipi_id: number
  vardiya_tipi_ad: string
  baslangic_saati: string
  bitis_saati: string
  gece_mi: boolean
  nokta_id: number
  nokta_ad: string
  degisim_tipi: DegisimTipi | null
}

export interface DonemOzeti {
  gece_sayisi: number
  ekip_ortalama_gece: number
  hafta_sonu_sayisi: number
  ekip_ortalama_hafta_sonu: number
  toplam_saat: number
  ekip_ortalama_saat: number
}

export interface Vardiyalarim {
  personel_id: number
  ad_soyad: string
  sicil_no: string
  yetkinlikler: string[]
  donem_id: number | null
  donem_baslangic_tarihi: string | null
  donem_bitis_tarihi: string | null
  surum_id: number | null
  yayinlanmis_surum_var: boolean
  yayin_zamani: string | null
  vardiyalar: Vardiyam[]
  siradaki: Vardiyam | null
  ozet: DonemOzeti | null
}

export interface AcikDonem {
  donem_id: number
  baslangic_tarihi: string
  bitis_tarihi: string
  tercih_son_tarihi: string
}

export interface CalisanTercih {
  tercih_id: number
  tarih: string
  tip: TercihTipi
  vardiya_tipi_id: number | null
  vardiya_tipi_ad: string | null
  calisan_notu: string | null
  durum: TercihDurumu
  ret_gerekcesi: string | null
  karsilanma: KarsilanmaDurumu
}

export interface CalisanTercihListesi {
  acik_donem: AcikDonem | null
  tercihler: CalisanTercih[]
}
