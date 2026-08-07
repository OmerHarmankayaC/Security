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
}
