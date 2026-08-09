import type {
  Analiz,
  Atama,
  AtamaDegisikligiIstek,
  Ben,
  Bina,
  CalisanTercihListesi,
  CalisanVardiyaTipi,
  CizelgeSurumu,
  CozumIsi,
  Donem,
  DogrulamaSonucu,
  GorevNoktasi,
  KapsamaAcigi,
  Kullanici,
  Kural,
  Musaitlik,
  MusaitlikOlusturIstek,
  OnKontrolBulgu,
  Personel,
  Rol,
  SurumKarsilastirmasi,
  TalepHucresi,
  TalepYaniti,
  TanimKullanimi,
  TanimYolu,
  Tercih,
  TercihDurumu,
  TercihTipi,
  Vardiyalarim,
  VardiyaTipi,
  Yetkinlik,
} from './types'

interface PersonelYazma {
  ad_soyad: string
  sicil_no: string
  haftalik_hedef_saat: number
  aktif_baslangic: string
  aktif_bitis?: string | null
  sabit_vardiya_tipi_id?: number | null
  yetkinlik_idleri?: number[]
}

export class ApiHatasi extends Error {
  status: number
  detay: unknown

  constructor(status: number, detay: unknown) {
    super(typeof detay === 'string' ? detay : `İstek başarısız (HTTP ${status})`)
    this.status = status
    this.detay = detay
  }
}

// Oturum düştüğünde (401) tek bir yerden haber verilir; kök bileşen buna
// abone olup giriş ekranına döner. Her ekranın 401'i kendi başına ele
// alması, birini atlayan ekranda kullanıcıyı boş bir sayfayla baş başa
// bırakırdı — oturum zaman aşımı her ekranda olabilir.
let _oturumDustuDinleyicisi: (() => void) | null = null

export function oturumDustugunde(dinleyici: (() => void) | null): void {
  _oturumDustuDinleyicisi = dinleyici
}

const GIRIS_YOLU = '/api/giris'

async function istek<T>(yol: string, secenekler?: RequestInit): Promise<T> {
  const yanit = await fetch(yol, {
    ...secenekler,
    headers: { 'Content-Type': 'application/json', ...secenekler?.headers },
  })
  if (!yanit.ok) {
    // Giriş isteğinin 401'i "oturum düştü" değil "kimlik bilgisi yanlış"tır;
    // dinleyiciye haber vermek, giriş ekranını kendi kendine sıfırlardı.
    if (yanit.status === 401 && yol !== GIRIS_YOLU) _oturumDustuDinleyicisi?.()
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
  donemOlustur: (govde: {
    baslangic_tarihi: string
    bitis_tarihi: string
    tercih_son_tarihi: string
  }) => gonder<Donem>('/api/donem', govde),
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
  // Silme her tanımda iki adımdır: önce /kullanim sorulur (kullanıcıya ne
  // olacağı söylenebilsin diye), sonra DELETE gönderilir. DELETE'in kendisi
  // aynı hesabı tekrar yapar; ön kontrol bir izin değil, bilgilendirmedir.
  tanimKullanimi: (yol: TanimYolu, id: number) =>
    istek<TanimKullanimi>(`/api/${yol}/${id}/kullanim`),
  tanimSil: (yol: TanimYolu, id: number) => silIste(`/api/${yol}/${id}`),

  yetkinlikListele: () => istek<Yetkinlik[]>('/api/yetkinlik'),
  yetkinlikOlustur: (ad: string, aciklama?: string) =>
    gonder<Yetkinlik>('/api/yetkinlik', { ad, aciklama: aciklama ?? null }),
  yetkinlikGuncelle: (id: number, veri: Partial<Pick<Yetkinlik, 'ad' | 'aciklama' | 'aktif'>>) =>
    gonder<Yetkinlik>(`/api/yetkinlik/${id}`, veri, 'PUT'),

  binaListele: () => istek<Bina[]>('/api/bina'),
  binaOlustur: (ad: string) => gonder<Bina>('/api/bina', { ad }),
  binaGuncelle: (id: number, veri: Partial<Pick<Bina, 'ad' | 'aktif'>>) =>
    gonder<Bina>(`/api/bina/${id}`, veri, 'PUT'),

  talepGetir: () => istek<TalepYaniti>('/api/talep'),
  talepHucresiGuncelle: (hucre: Omit<TalepHucresi, 'talep_id'>) =>
    gonder<TalepYaniti>('/api/talep', hucre, 'PUT'),

  kuralListele: () => istek<Kural[]>('/api/kural'),
  // Kuralda DELETE yoktur: H1–H8 ve S1–S8 modelin yapısını oluşturur ve
  // kayıt defterindeki sınıflarla eşleşir (SDD 3.2.1). Devre dışı bırakma
  // `aktif` alanıyla yapılır.
  kuralGuncelle: (
    kimlik: string,
    veri: Partial<Pick<Kural, 'agirlik' | 'aktif' | 'parametreler'>>,
  ) => gonder<Kural>(`/api/kural/${kimlik}`, veri, 'PUT'),

  personelOlustur: (govde: PersonelYazma) => gonder<Personel>('/api/personel', govde),
  personelGuncelle: (id: number, govde: Partial<PersonelYazma>) =>
    gonder<Personel>(`/api/personel/${id}`, govde, 'PUT'),

  noktaOlustur: (ad: string, binaId: number | null, onkosulYetkinlikId: number | null) =>
    gonder<GorevNoktasi>('/api/nokta', {
      ad,
      bina_id: binaId,
      onkosul_yetkinlik_id: onkosulYetkinlikId,
    }),
  noktaGuncelle: (
    id: number,
    veri: Partial<Pick<GorevNoktasi, 'ad' | 'bina_id' | 'onkosul_yetkinlik_id' | 'aktif'>>,
  ) => gonder<GorevNoktasi>(`/api/nokta/${id}`, veri, 'PUT'),

  vardiyaTipiOlustur: (ad: string, baslangicSaati: string, bitisSaati: string) =>
    gonder<VardiyaTipi>('/api/vardiya-tipi', {
      ad,
      baslangic_saati: baslangicSaati,
      bitis_saati: bitisSaati,
    }),
  vardiyaTipiGuncelle: (
    id: number,
    veri: Partial<Pick<VardiyaTipi, 'ad' | 'baslangic_saati' | 'bitis_saati' | 'gece_mi' | 'aktif'>>,
  ) => gonder<VardiyaTipi>(`/api/vardiya-tipi/${id}`, veri, 'PUT'),

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

  // --- Sürümler (FR-7.x, SDD 6.3.5) ---------------------------------------
  surumYayinla: (surumId: number) => gonder<CizelgeSurumu>(`/api/surum/${surumId}/yayinla`, {}),
  surumTaslakTuret: (oncekiSurumId: number) =>
    gonder<CizelgeSurumu>('/api/surum', { onceki_surum_id: oncekiSurumId }),
  // Türetmeden farkı atamaların KOPYALANMASI: `surumTaslakTuret` çözücünün
  // dolduracağı boş bir taslak açar, bu kaynağın çizelgesini olduğu gibi
  // taşır. Kaynak sürüm her iki durumda da değişmez.
  surumTaslakOlarakKopyala: (kaynakSurumId: number) =>
    gonder<CizelgeSurumu>(`/api/surum/${kaynakSurumId}/kopyala`, {}),
  surumKarsilastir: (oncekiSurumId: number, yeniSurumId: number) =>
    istek<SurumKarsilastirmasi>(
      `/api/surum/karsilastir?onceki_surum_id=${oncekiSurumId}&yeni_surum_id=${yeniSurumId}`,
    ),

  // --- Analiz (FR-8.x) ---------------------------------------------------
  analizGetir: (surumId: number) => istek<Analiz>(`/api/analiz/${surumId}`),

  // --- Çalışan Paneli (SDD 6.1, Ek B; SRS FR-9.x) -------------------------
  // Hiçbiri `personel_id` GÖNDERMEZ ve göndermemelidir: hangi personelin
  // verisinin döneceği sunucuda yalnızca oturumdan belirlenir (FR-9.1).
  // Kimliği burada taşımak, sunucunun onu yok saydığı bilinse bile,
  // "istemci kimliği seçiyor" izlenimi verirdi.
  calisanVardiyalarim: () => istek<Vardiyalarim>('/api/calisan/vardiyalarim'),
  calisanTercihlerim: () => istek<CalisanTercihListesi>('/api/calisan/tercih'),
  calisanTercihBildir: (govde: {
    tarih: string
    tip: TercihTipi
    vardiya_tipi_id?: number | null
    calisan_notu?: string | null
  }) => gonder('/api/calisan/tercih', govde),
  // Tanımlar yönlendiricisindeki `/api/vardiya-tipi` çalışan rolüne kapalı
  // (SRS 5.10); tercih formunun ihtiyacı olan liste çalışan yüzeyinin
  // kendi ucundan gelir.
  calisanVardiyaTipleri: () => istek<CalisanVardiyaTipi[]>('/api/calisan/vardiya-tipi'),

  // --- Kimlik (SRS FR-10.1, FR-10.3, FR-10.7) -----------------------------
  // Belirteç HttpOnly çerezde taşınır; JavaScript onu ne okur ne yazar.
  // Bu yüzden burada bir "token" parametresi yoktur ve olmayacaktır.
  // Kayıt uç noktası da yoktur (FR-10.1): hesapları yönetim rolü açar.
  giris: (kullaniciAdi: string, parola: string) =>
    gonder<Ben>('/api/giris', { kullanici_adi: kullaniciAdi, parola }),
  cikis: () => gonder<void>('/api/cikis', {}),
  ben: () => istek<Ben>('/api/ben'),
  parolaDegistir: (mevcutParola: string, yeniParola: string) =>
    gonder<Ben>('/api/parola-degistir', {
      mevcut_parola: mevcutParola,
      yeni_parola: yeniParola,
    }),

  // --- Hesap yönetimi (yalnız yönetim rolü — SRS FR-10.5) -----------------
  // Silme YOKTUR: hesap devre dışı bırakılır, kayıt durur.
  kullaniciListele: () => istek<Kullanici[]>('/api/kullanici'),
  kullaniciOlustur: (govde: {
    kullanici_adi: string
    parola: string
    rol: Rol
    personel_id?: number | null
  }) => gonder<Kullanici>('/api/kullanici', govde),
  kullaniciGuncelle: (
    kullaniciId: number,
    govde: { rol?: Rol; aktif?: boolean; personel_id?: number | null },
  ) => gonder<Kullanici>(`/api/kullanici/${kullaniciId}`, govde, 'PUT'),
  kullaniciParolaSifirla: (kullaniciId: number, yeniParola: string) =>
    gonder<Kullanici>(`/api/kullanici/${kullaniciId}/parola-sifirla`, {
      yeni_parola: yeniParola,
    }),
}
