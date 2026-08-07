import type {
  Analiz,
  Atama,
  AtamaDegisikligiIstek,
  Bina,
  CalisanTercihListesi,
  CizelgeSurumu,
  CozumIsi,
  Donem,
  DogrulamaSonucu,
  GorevNoktasi,
  KapsamaAcigi,
  Kural,
  Musaitlik,
  MusaitlikOlusturIstek,
  OnKontrolBulgu,
  Personel,
  TalepHucresi,
  TalepYaniti,
  Tercih,
  TercihDurumu,
  TercihTipi,
  Vardiyalarim,
  VardiyaTipi,
  Yetkinlik,
} from './types'

export class ApiHatasi extends Error {
  status: number
  detay: unknown

  constructor(status: number, detay: unknown) {
    super(typeof detay === 'string' ? detay : `İstek başarısız (HTTP ${status})`)
    this.status = status
    this.detay = detay
  }
}

async function istek<T>(yol: string, secenekler?: RequestInit): Promise<T> {
  const yanit = await fetch(yol, {
    ...secenekler,
    headers: { 'Content-Type': 'application/json', ...secenekler?.headers },
  })
  if (!yanit.ok) {
    const govde = await yanit.json().catch(() => null)
    throw new ApiHatasi(yanit.status, govde?.detail ?? govde)
  }
  if (yanit.status === 204) return undefined as T
  return (await yanit.json()) as T
}

const gonder = <T>(yol: string, govde: unknown, yontem: 'POST' | 'PUT' = 'POST') =>
  istek<T>(yol, { method: yontem, body: JSON.stringify(govde) })

const silIste = (yol: string) => istek<void>(yol, { method: 'DELETE' })

export const api = {
  donemler: () => istek<Donem[]>('/api/donem'),
  surumler: (donemId: number) => istek<CizelgeSurumu[]>(`/api/surum?donem_id=${donemId}`),
  surumAtamalari: (surumId: number) => istek<Atama[]>(`/api/surum/${surumId}/atama`),
  surumKapsamaAcigi: (surumId: number) =>
    istek<KapsamaAcigi[]>(`/api/surum/${surumId}/kapsama-acigi`),

  personelListele: () => istek<Personel[]>('/api/personel'),
  vardiyaTipiListele: () => istek<VardiyaTipi[]>('/api/vardiya-tipi'),
  noktaListele: () => istek<GorevNoktasi[]>('/api/nokta'),

  onKontrolCalistir: (donemId: number) =>
    gonder<{ bulgular: OnKontrolBulgu[] }>('/api/on-kontrol', { donem_id: donemId }),
  cozumBaslat: (donemId: number, zamanLimitiSaniye: number) =>
    gonder<CozumIsi>('/api/cozum', {
      donem_id: donemId,
      zaman_limiti_saniye: zamanLimitiSaniye,
    }),
  cozumDurumu: (isId: number) => istek<CozumIsi>(`/api/cozum/${isId}`),
  cozumIptalEt: (isId: number) => gonder<CozumIsi>(`/api/cozum/${isId}/iptal`, {}),

  atamaDogrula: (istekGovdesi: AtamaDegisikligiIstek) =>
    gonder<DogrulamaSonucu>('/api/atama/dogrula', istekGovdesi),
  atamaGuncelle: (istekGovdesi: AtamaDegisikligiIstek) =>
    gonder<DogrulamaSonucu>('/api/atama', istekGovdesi, 'PUT'),
  atamaKilitAyarla: (
    surumId: number,
    personelId: number,
    tarih: string,
    kilitli: boolean,
  ) =>
    gonder<Atama>('/api/atama/kilit', {
      surum_id: surumId,
      personel_id: personelId,
      tarih,
      kilitli,
    }),

  // --- Tanımlar (Sprint 3 Ara İş) -----------------------------------------
  yetkinlikListele: () => istek<Yetkinlik[]>('/api/yetkinlik'),
  yetkinlikOlustur: (ad: string, aciklama?: string) =>
    gonder<Yetkinlik>('/api/yetkinlik', { ad, aciklama: aciklama ?? null }),

  binaListele: () => istek<Bina[]>('/api/bina'),
  binaOlustur: (ad: string) => gonder<Bina>('/api/bina', { ad }),

  talepGetir: () => istek<TalepYaniti>('/api/talep'),
  talepHucresiGuncelle: (hucre: Omit<TalepHucresi, 'talep_id'>) =>
    gonder<TalepYaniti>('/api/talep', hucre, 'PUT'),

  kuralListele: () => istek<Kural[]>('/api/kural'),
  kuralGuncelle: (kimlik: string, veri: Partial<Pick<Kural, 'agirlik' | 'aktif'>>) =>
    gonder<Kural>(`/api/kural/${kimlik}`, veri, 'PUT'),

  personelOlustur: (govde: {
    ad_soyad: string
    sicil_no: string
    haftalik_hedef_saat: number
    aktif_baslangic: string
    yetkinlik_idleri?: number[]
  }) => gonder<Personel>('/api/personel', govde),

  noktaOlustur: (ad: string, binaId: number | null, onkosulYetkinlikId: number | null) =>
    gonder<GorevNoktasi>('/api/nokta', {
      ad,
      bina_id: binaId,
      onkosul_yetkinlik_id: onkosulYetkinlikId,
    }),

  vardiyaTipiOlustur: (ad: string, baslangicSaati: string, bitisSaati: string) =>
    gonder<VardiyaTipi>('/api/vardiya-tipi', {
      ad,
      baslangic_saati: baslangicSaati,
      bitis_saati: bitisSaati,
    }),

  // --- Müsaitlik (FR-2.x) --------------------------------------------------
  musaitlikListele: () => istek<Musaitlik[]>('/api/musaitlik'),
  musaitlikOlustur: (govde: MusaitlikOlusturIstek) => gonder<Musaitlik>('/api/musaitlik', govde),
  musaitlikSil: (musaitlikId: number) => silIste(`/api/musaitlik/${musaitlikId}`),

  // --- Tercih (FR-3.x) -------------------------------------------------------
  tercihListele: () => istek<Tercih[]>('/api/tercih'),
  tercihOlustur: (govde: {
    personel_id: number
    donem_id: number
    tarih: string
    tip: TercihTipi
    vardiya_tipi_id?: number | null
  }) => gonder<Tercih>('/api/tercih', govde),
  tercihDurumGuncelle: (tercihId: number, durum: TercihDurumu, retGerekcesi?: string) =>
    gonder<Tercih>(
      `/api/tercih/${tercihId}`,
      { durum, ...(retGerekcesi ? { ret_gerekcesi: retGerekcesi } : {}) },
      'PUT',
    ),

  // --- Analiz (FR-8.x) ---------------------------------------------------
  analizGetir: (surumId: number) => istek<Analiz>(`/api/analiz/${surumId}`),

  // --- Çalışan Paneli (SDD 6.1, Ek B; SRS FR-9.x) -------------------------
  calisanVardiyalarim: (personelId: number, anahtar: string) =>
    istek<Vardiyalarim>(
      `/api/calisan/vardiyalarim?personel_id=${personelId}&anahtar=${encodeURIComponent(anahtar)}`,
    ),
  calisanTercihlerim: (personelId: number, anahtar: string) =>
    istek<CalisanTercihListesi>(
      `/api/calisan/tercih?personel_id=${personelId}&anahtar=${encodeURIComponent(anahtar)}`,
    ),
  calisanTercihBildir: (
    personelId: number,
    anahtar: string,
    govde: { tarih: string; tip: TercihTipi; vardiya_tipi_id?: number | null; calisan_notu?: string | null },
  ) =>
    gonder(
      `/api/calisan/tercih?personel_id=${personelId}&anahtar=${encodeURIComponent(anahtar)}`,
      govde,
    ),
}
