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
  olusturma_zamani: string
  guncelleme_zamani: string
  /**
   * Sürüm damgası — eş zamanlı düzenlemeyi yakalar (SRS TD-16, SDD 5.5.1).
   *
   * Kullanıcı düzenlemeye başlarken bu değeri alır, kaydederken geri
   * gönderir. Damga değişmişse başka bir oturum aynı sürümü değiştirmiştir
   * ve kayıt reddedilir; sessizce üzerine yazmak diğerinin işini iz
   * bırakmadan yok ederdi. İstemci için ANLAMSIZ bir dizedir — yorumlanmaz,
   * yalnızca taşınır.
   */
  damga: string
  // SDD 6.3.5 — Sürümler ekranının liste satırı bu ikisini de gösterir.
  // Hiç çözülmemiş bir taslakta toplam_ceza null olur.
  toplam_ceza: number | null
  // Açık hücre sayısı değil, toplam eksik KİŞİ sayısı.
  kapsama_acigi_sayisi: number
  // Talepten FAZLA yazılmış toplam kişi sayısı (SRS 4.3 S1 üst sınırı).
  // Kapsama açığıyla toplanmaz: iki zıt yöndeki sapmayı tek sayıda
  // gizlemek "3 açık" ile "3 fazla"yı aynı gösterirdi.
  fazla_kadro_sayisi: number
}

// --- Sürümler / Karşılaştır (SDD 6.3.5) -------------------------------------

export type AtamaFarkiTuru = 'eklendi' | 'kaldirildi' | 'degisti'

export interface AtamaFarki {
  personel_id: number
  ad_soyad: string
  tarih: string
  tur: AtamaFarkiTuru
  /** Blok adı diye bir şey yok (SRS TD-13); karşılaştırma bloğun ZAMAN
   *  ARALIĞINI gösterir ("08.00–16.00"). */
  onceki_blok: string | null
  onceki_nokta_ad: string | null
  yeni_blok: string | null
  yeni_nokta_ad: string | null
}

export interface SurumKarsilastirmasi {
  onceki_surum_id: number
  yeni_surum_id: number
  onceki_surum_no: number
  yeni_surum_no: number
  eklenen: number
  kaldirilan: number
  degisen: number
  // Charter bölüm 5, altıncı kabul kriteri: "değişen atama sayısı raporlanır".
  toplam_degisiklik: number
  farklar: AtamaFarki[]
}

export type AtamaKaynagi = 'cozucu' | 'manuel'

/**
 * Bir çalışma bloğu (SDD 4.2.1).
 *
 * `tarih` ve `sure_saat` sunucuda TÜRETİLİR, saklanmaz: blok başladığı güne
 * sayılır (SRS TD-1) ve ızgara satırları o güne göre gruplanır. Gece yarısını
 * aşan blokta `bitis_zamani` ertesi güne düşer.
 */
export interface Atama {
  atama_id: number
  personel_id: number
  baslangic_zamani: string
  bitis_zamani: string
  tarih: string
  sure_saat: number
  nokta_id: number
  kilitli: boolean
  kaynak: AtamaKaynagi
}

export interface KapsamaAcigi {
  acik_id: number
  /**
   * ZAMAN DAMGASI (B-23). Önceki hâli `tarih` + ofsetsiz `baslangic`/`bitis`
   * taşıyordu; o gösterimde 22.00–02.00 gibi bir aralık tek kayıtta duramıyor
   * ve dosyaya ISO damgası olarak yazılamıyordu. Aralık artık gün sınırını
   * kendisi taşır; kaydın hangi güne ait olduğu başlangıç damgasından okunur.
   */
  baslangic_zamani: string
  bitis_zamani: string
  nokta_id: number
  eksik_sayi: number
}

/** Bir noktaya talepten fazla kişi atanmış olması (SRS 4.3 S1 üst sınırı). */
export interface FazlaKadro {
  fazla_id: number
  baslangic_zamani: string
  bitis_zamani: string
  nokta_id: number
  fazla_sayi: number
}

export interface Personel {
  personel_id: number
  ad_soyad: string
  sicil_no: string
  haftalik_hedef_saat: number
  aktif_baslangic: string
  aktif_bitis: string | null
  yetkinlik_idleri: number[]
  /**
   * Devir bakiyesi (SRS FR-1.1). NUMERIC olduğu için metin gelir. Bu turda
   * hiçbir kural okumaz; forma girilmesinin nedeni verinin Tur 4'te kota
   * hesabına hazır olmasıdır.
   */
  devir_fazla_calisma_saat: string
  kota_yili: number | null
}

/** Resmî tatil işareti (FR-1.10). Anahtar tarihin kendisidir (SDD 4.2.1). */
export interface OzelGun {
  tarih: string
  ad: string
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
  // Arama sonlandı, sonuç saklandı, KULLANICI KARARI bekleniyor. Terminal
  // bir durum değildir (SDD 5.4.1).
  | 'durduruldu'
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
  // "Devam et" kararıyla açılmış işlerde, ipucunun alındığı önceki iş.
  devam_kaynagi_is_id: number | null
  // Geçici sonucun KENDİSİ değil, yalnızca var olup olmadığı — sunucu onu
  // hiçbir okuma yüzeyine vermez (SDD 4.2.4). Arayüzün tek ihtiyacı,
  // "Sonucu kullan" seçeneğini etkinleştirip etkinleştirmeyeceğidir.
  kullanilabilir_sonuc_var: boolean
  // Karar panelinin gösterdiği kapsama açığı sayısı; yine içerik değil özet.
  gecici_kapsama_acigi_sayisi: number | null
}

export type CozumKarari = 'kullan' | 'at' | 'devam'

export interface CozumKarariYaniti {
  is_kaydi: CozumIsi
  yeni_is: CozumIsi | null
}

export type OnKontrolBulguTipi =
  | 'donem_kapasitesi'
  | 'yetkinlik_havuzu'
  | 'gunluk_musaitlik'
  | 'nokta_musaitlik'
  | 'kapsama_kurali_pasif'
  // Kota bulguları (SDD 5.2, Tur 4). İkisi de bulgudur, engel değil.
  | 'devir_kotayi_asmis'
  | 'kotasi_dolmus_personel'

export interface OnKontrolBulgu {
  tip: OnKontrolBulguTipi
  // false ise bulgu çözümü DURDURMAZ: yapısal engel değil, yapılandırma
  // uyarısı (ör. S1 pasif). Arayüz ikisini ayrı gösterir.
  kesin_mi: boolean
  aciklama: string
  eksik: number | null
  yetkinlik_id: number | null
  tarih: string | null
  /** Bulgu artık bir vardiya TİPİNİ değil bir SAATİ gösterir (SRS TD-13). */
  saat: number | null
  nokta_id: number | null
  personel_id: number | null
}

export interface Ihlal {
  kural_kimlik: string
  aciklama: string
  personel_id: number | null
  tarih: string | null
  ceza: number | null
}

/** Bir esnek hedefin ceza değişimi, ağırlığıyla birlikte (FR-4.8). */
export interface CezaKalemi {
  kural_kimlik: string
  ad: string
  ham_fark: number
  agirlik: number
  agirlikli_fark: number
}

export interface DogrulamaSonucu {
  kabul_edilebilir: boolean
  zorunlu_ihlaller: Ihlal[]
  /** Ham (ağırlıksız) toplam. Ekranda GÖSTERİLMEZ: farklı birimlerdeki
   *  cezaları (kişi, vardiya, saat, gün) ağırlıksız topladığı için
   *  büyüklükleri karşılaştırılabilir değil. */
  ceza_degisimi: number
  agirlikli_ceza_degisimi: number
  ceza_dokumu: CezaKalemi[]
  /** Değişikliğin yeni doğurduğu, bir yere işaret eden esnek bulgular
   *  (kapsama açığı, fazla kadro). Zorunlu ihlal DEĞİLDİR — değişiklik
   *  uygulanır, karar kullanıcıya bırakılır (SDD 5.5). */
  uyarilar: Ihlal[]
  /** Kaydetme yanıtında YENİ damga; doğrulama yanıtında null (hiçbir şey
   *  yazılmadığı için damga da değişmez). */
  damga?: string | null
}

/**
 * Izgaradaki bir (personel, gün) satırına yazılan blok (SDD 6.3.3).
 *
 * Üçü de boş ise o günün bloğu kaldırılır; üçü de doluysa günün bloğu bu olur.
 * Saatler saat başında olmalıdır — saat ekseni yarım saatlik sınırları temsil
 * edemez (SDD 6.3.1). Bitiş başlangıçtan küçük ya da eşitse blok gece yarısını
 * aşar.
 */
export interface BlokDegisikligi {
  personel_id: number
  tarih: string
  baslangic_saati: string | null
  bitis_saati: string | null
  nokta_id: number | null
}

/**
 * Doğrulama isteği: oturumun O ANA KADAR biriken TAMAMI (SRS TD-16).
 *
 * Son değişikliği değil bütün birikimi taşır. Tek tek geçerli olan iki
 * değişiklik birlikte bir kuralı bozabilir: iki ayrı güne yapılan uzatma,
 * ayrı ayrı haftalık tavanı aşmazken birlikte aşar.
 */
export interface DogrulamaIstegi {
  surum_id: number
  degisiklikler: BlokDegisikligi[]
}

/** Kaydetme: doğrulama isteği + sürüm damgası (SDD 5.5.1). */
export interface KaydetIstegi extends DogrulamaIstegi {
  damga: string
}

// --- Tanımlar (Sprint 3 Ara İş) --------------------------------------------

// Tanım varlıklarının API yolu. Silme ve kullanım sorgusu beş varlıkta da aynı
// biçimde çalıştığından tek bir yol üzerinden geçer.
export type TanimYolu = 'yetkinlik' | 'bina' | 'nokta' | 'personel'

export interface TanimKullanimiKalemi {
  kayit_turu: string
  sayi: number
}

// Silmeden ÖNCE sorulur: kullanımda olan bir tanım silinmez, pasifleştirilir.
// Onay kutusunun metni bundan kurulur.
export interface TanimKullanimi {
  kullanimda_mi: boolean
  toplam: number
  kalemler: TanimKullanimiKalemi[]
}

export interface Yetkinlik {
  yetkinlik_id: number
  ad: string
  aciklama: string | null
  aktif: boolean
}

export interface Bina {
  bina_id: number
  ad: string
  aktif: boolean
}

export type GunTipi = 'hafta_ici' | 'hafta_sonu' | 'resmi_tatil'

/**
 * Bir talep ARALIĞI (SDD 4.2.2). Talep bir vardiya bloğuna değil bir zaman
 * aralığına bağlıdır; `baslangic`/`bitis` "HH:MM:SS" biçiminde gelir.
 *
 * Gün sonu `00:00:00` ile yazılır: `bitis <= baslangic` ise aralık gün
 * sonuna kadar sürer ya da gece yarısını aşar. Ekranda 24.00 gösterilir
 * (bkz. lib/talepAraligi.ts).
 */
export interface TalepAraligi {
  talep_id: number
  nokta_id: number
  gun_tipi: GunTipi
  /** Doluysa bu satır YALNIZCA o tarih için geçerli bir istisnadır. */
  tarih: string | null
  baslangic: string
  bitis: string
  gereken_sayi: number
}

/** Ekleme/düzenleme gövdesi — kimliksiz aralık. */
export type TalepAraligiYazma = Omit<TalepAraligi, 'talep_id'>

export interface YukGostergesi {
  haftalik_kisi_saat: string
  asgari_kadro: number
}

export interface TalepYaniti {
  araliklar: TalepAraligi[]
  yuk_gostergesi: YukGostergesi
}

export type KuralTipi = 'zorunlu' | 'esnek'

// Parametreler veritabanında belge alanında durur (SDD 4.2.3) — her kuralın
// parametre kümesi farklı. Ham JSON göstermek yerine alan-değer olarak
// düzenlenebilmesi için şema kural sınıfından gelir (SDD 3.2.1).
export interface ParametreTanimi {
  anahtar: string
  etiket: string
  birim: string | null
  asgari: number | null
  azami: number | null
}

export interface Kural {
  kural_id: number
  kimlik: string
  tip: KuralTipi
  parametreler: Record<string, unknown>
  agirlik: number | null
  aktif: boolean
  // Katalog bilgisi (SRS bölüm 4), kayıt defterinden okuma anında eklenir.
  ad: string
  aciklama: string
  parametre_tanimlari: ParametreTanimi[]
  // H1–H8 ve S1–S8 modelin yapısını oluşturur; silinemez, yalnızca
  // pasifleştirilir. Kayıt defterinde sınıfı olmayan bir kural zaten
  // yüklenemediğinden bu alan bugün her katalog kuralında false'tur.
  silinebilir_mi: boolean
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

export type TercihTipi = 'calismama' | 'zaman_araligi_tercihi'
export type TercihDurumu = 'beklemede' | 'onaylandi' | 'reddedildi'

export interface Tercih {
  tercih_id: number
  personel_id: number
  donem_id: number
  tarih: string
  tip: TercihTipi
  /** Zaman aralığı tercihinde istenen aralık; çalışmama tercihinde boş. */
  tercih_baslangic: string | null
  tercih_bitis: string | null
  durum: TercihDurumu
  calisan_notu: string | null
  ret_gerekcesi: string | null
}

// --- Analiz (FR-8.x, SDD 5.7) -----------------------------------------------

/**
 * Kişi başına bir metriğin değeri.
 *
 * `sayi`nın BİRİMİ ÖLÇÜYE GÖRE DEĞİŞİR: gece ve hafta sonu dağılımlarında
 * SAAT (SRS S2/S3 — blok süreleri çözümün çıktısı olduğundan sayıma dayalı
 * bir ölçü tanımsızdır), bina değişim sayacında ADET.
 */
export interface KisiSayisi {
  personel_id: number
  ad_soyad: string
  sayi: number
  /**
   * Kişiye düşen ADİL PAY — ölçünün referansı (SRS S2/S3).
   *
   * Havuz ortalaması DEĞİLDİR ve onun yerine geçer: erişilebilirliği kısıtlı
   * bir havuz tek ortalamaya vurulduğunda kalıcı olarak sapmalı görünür ve
   * ölçü ayırt edici olmaktan çıkar. Payı bulunmayan ölçülerde (bina değişim
   * sayacı) `null`dur — orada adil pay diye bir kavram yok.
   */
  pay: number | null
}

export interface SaatDengesi {
  personel_id: number
  ad_soyad: string
  toplam_saat: number
  hedef_saat: number
  sapma: number
}

/** Analiz ekranının fazla kadro satırı — adlarıyla birlikte (NFR-5). */
export interface FazlaKadroKalemi {
  baslangic_zamani: string
  bitis_zamani: string
  nokta_id: number
  nokta_ad: string
  fazla_sayi: number
}

export interface Analiz {
  surum_id: number
  kapsama_orani: number
  /** Kapsama oranından AYRI: oran "talebin ne kadarı karşılandı" sorusunu
   *  yanıtlar, fazla kadro o soruya bir şey eklemez. */
  fazla_kadro: FazlaKadroKalemi[]
  toplam_fazla_kadro: number
  kisi_basina_gece: KisiSayisi[]
  kisi_basina_hafta_sonu: KisiSayisi[]
  saat_dagilimi: SaatDengesi[]
  en_dengesiz_personel_id: number | null
  en_dengesiz_ad_soyad: string | null
  tercih_karsilama_orani: number | null
  bina_degisim_sayisi: KisiSayisi[]
  ceza_dokumu: Record<string, number> | null
  toplam_ceza: number | null
  /** ARALIK SAYISI ile KİŞİ-SAAT ayrı ölçülerdir (SDD 6.3.4): ardışık saatler
   *  tek kayıtta birleştiği için satır sayısı yükü anlatmaz. İkisi karıştırıldı
   *  ve dışa aktarma başlığında yanlış sayı gösterildi. */
  karsilanmayan_kisi_saat: number
  acik_aralik_sayisi: number
  kota_durumu: KotaDurumu[]
  ceza_kalemleri: AnalizCezaKalemi[]
  kumulatif_degisim: KumulatifDegisim
  /** Hangi ufkun ölçüldüğü. İki ufkun sayıları farklıdır ve hangisine
   *  bakıldığı belirsiz kalırsa tablo yanlış okunur. */
  ufuk: Ufuk
}

export type Ufuk = 'donem' | 'adalet'

/** H10: kişi başına yıllık fazla çalışma ve kalan kota. Sunucu SIRALI
 *  gönderir — sınıra dayanan üstte; kartın amacı listeyi değil riski
 *  göstermek (SDD 6.3.4). */
export interface KotaDurumu {
  personel_id: number
  ad_soyad: string
  fazla_calisma_saat: number
  kalan_kota_saat: number
}

/** Analiz ekranının ceza dökümü satırı (SDD 6.3.4). Doğrulama sonucundaki
 *  `CezaKalemi`den AYRIDIR: o bir değişikliğin FARKINI taşır, bu ise sürümün
 *  mevcut durumunu. Ham değer kuralın kendi biriminde (kişi-saat, saat, gün);
 *  ağırlıklı ceza amaç fonksiyonuna girendir. İkisinin tek sütunda
 *  gösterilmesi, toplamın satırların toplamı olmadığı bir tablo üretir. */
export interface AnalizCezaKalemi {
  kimlik: string
  ad: string
  ham_deger: number
  agirlik: number
  agirlikli_ceza: number
}

/** Kümülatif adaletin vaadi sapmanın küçük olması değil, ZAMANLA küçülmesidir
 *  (Charter 5, K3). Önceki yayınlanmış dönem yoksa alanlar null kalır —
 *  sıfır yazmak "değişim olmadı" anlamına gelirdi. */
export interface KumulatifDegisim {
  onceki_surum_id: number | null
  onceki_ortalama_sapma: number | null
  simdiki_ortalama_sapma: number | null
}

// --- Çalışan Paneli (SDD 6.1, Ek B; SRS FR-9.x) -----------------------------

// FR-9.4'ün üç değişim türünden ikisi; üçüncüsü ("kaldırıldı") bir vardiya
// üzerinde taşınamaz, çünkü o gün artık vardiya yoktur — bkz. KaldirilanGun.
export type DegisimTipi = 'eklendi' | 'degisti'
export type KarsilanmaDurumu = 'karsilandi' | 'karsilanmadi' | 'henuz_belirsiz'

/**
 * Çalışanın bir günlük çalışma bloğu.
 *
 * Blok adı diye bir şey yok (SRS TD-13); çalışanın görmesi gereken bilgi
 * saatin kendisidir. `gece_saati` HESAPLANIR (TD-2), işaretlenmez.
 */
export interface Vardiyam {
  tarih: string
  baslangic_zamani: string
  bitis_zamani: string
  sure_saat: number
  gece_saati: number
  nokta_id: number
  nokta_ad: string
  degisim_tipi: DegisimTipi | null
}

// FR-9.4 üçüncü tür: arşiv sürümünde o gün atama vardı, yayınlanmışta yok.
// `Vardiyam` listesine karıştırılmaz — vardiya sayısı, "sıradaki vardiyan" ve
// dönem ızgarasının dolu hücreleri yalnızca gerçek vardiyalardan beslenir.
export interface KaldirilanGun {
  tarih: string
  onceki_baslangic_zamani: string
  onceki_bitis_zamani: string
  onceki_nokta_ad: string
}

export interface DonemOzeti {
  /** Birim SAAT (SRS S2, S3). */
  gece_saati: number
  ekip_ortalama_gece: number
  // SRS S2/S3'teki uygun havuz (P_gece / P_hs) üyeliği. Havuz dışındaki
  // çalışan o vardiyaları yetkinliği gereği hiç alamaz; karşılaştırma
  // anlamsız olduğu için gösterilmez (SDD 5.7).
  gece_havuzunda: boolean
  hafta_sonu_saati: number
  ekip_ortalama_hafta_sonu: number
  hafta_sonu_havuzunda: boolean
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
  kaldirilan_gunler: KaldirilanGun[]
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
  tercih_baslangic: string | null
  tercih_bitis: string | null
  calisan_notu: string | null
  durum: TercihDurumu
  ret_gerekcesi: string | null
  // TD-12: karşılanma yalnızca ONAYLANMIŞ tercihler için türetilir; bekleyen
  // ya da reddedilmiş bir tercihte tanımsızdır (null) ve gösterilmez.
  karsilanma: KarsilanmaDurumu | null
}

export interface CalisanTercihListesi {
  acik_donem: AcikDonem | null
  tercihler: CalisanTercih[]
}

// --- Kimlik ve hesaplar (SRS 5.10, FR-10.x) --------------------------------

export type Rol = 'calisan' | 'yonetici' | 'yonetim'

/** `/api/ben` — giriş yapan kullanıcının kendi tanımı. */
export interface Ben {
  kullanici_adi: string
  rol: Rol
  parola_degistirmeli: boolean
  // Bilgilendirme amaçlı. Çalışan isteklerinde hangi personelin verisinin
  // döneceği SUNUCUDA oturumdan belirlenir (FR-9.1); bu alanın istemciye
  // dönmesi o seçime hiçbir şekilde girmez.
  personel_id: number | null
  ad_soyad: string | null
}

export interface Kullanici {
  kullanici_id: number
  kullanici_adi: string
  rol: Rol
  personel_id: number | null
  ad_soyad: string | null
  aktif: boolean
  parola_degistirmeli: boolean
  kilitli_mi: boolean
}

