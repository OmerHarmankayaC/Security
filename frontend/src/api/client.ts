import type {
  Atama,
  AtamaDegisikligiIstek,
  CizelgeSurumu,
  CozumIsi,
  Donem,
  DogrulamaSonucu,
  GorevNoktasi,
  KapsamaAcigi,
  OnKontrolBulgu,
  Personel,
  VardiyaTipi,
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
}
