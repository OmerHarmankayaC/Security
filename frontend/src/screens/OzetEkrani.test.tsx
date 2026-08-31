/**
 * Özet ekranının davranış testleri (SDD 6.3.1, Görev 7).
 *
 * Ekranın sorusu "şu an ne oluyor" — dönem seçici YOK, dönem `donemSec()`
 * ile bugünden türetilir. Bunun karşılığı: her aralık-bağlı blok hangi
 * aralığı gösterdiğini metin olarak taşımalı. Burada ölçülen DAVRANIŞ;
 * yerleşim ve okunabilirlik insan gözü ister (bkz. AnalizEkrani.test.tsx
 * aynı notu taşır).
 */
import { cleanup, fireEvent, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type {
  Analiz,
  CizelgeSurumu,
  GorevNoktasi,
  KapsamaAcigi,
  Musaitlik,
  Personel,
  Tercih,
} from '../api/types'

import { OzetEkrani } from './OzetEkrani'
import { ciz } from '@/test/ciz'
import { BOS } from '@/lib/sayi'

// AppShell oturum bağlamı ister ve bu testlerin konusu değil; çocuklarını
// döken bir kabukla değiştirilir (bkz. AnalizEkrani.test.tsx).
vi.mock('../components/AppShell', () => ({
  AppShell: ({ children }: { children: unknown }) => <div>{children as never}</div>,
}))

const DONEM = { donem_id: 1, baslangic_tarihi: '2026-08-17', bitis_tarihi: '2026-08-23', tercih_son_tarihi: '2026-08-10' }

const PERSONEL: Personel[] = [
  { personel_id: 1, ad_soyad: 'Elif Aydın' } as never,
  { personel_id: 2, ad_soyad: 'Mert Can' } as never,
]

const NOKTALAR: GorevNoktasi[] = [
  { nokta_id: 1, ad: 'Nöbet Masası', bina_id: null, onkosul_yetkinlik_id: null, aktif: true },
  { nokta_id: 2, ad: 'Kapı Güvenliği', bina_id: null, onkosul_yetkinlik_id: null, aktif: true },
]

// Gün 20 (BUGÜN) iki kayıt taşır (aralık 08.00-14.00 + 14.00-18.00 → 10
// kişi-saat), gün 18 bir kayıt (4 kişi-saat), gün 22 bir kayıt (3 kişi-saat).
// gunluk_kapsama toplamı (4+10+3=17) karsilanmayan_kisi_saat'e eşit —
// backend sözleşmesiyle (SDD 6.3.1) tutarlı kalsın diye.
const KAPSAMA_ACIGI: KapsamaAcigi[] = [
  {
    acik_id: 1,
    baslangic_zamani: '2026-08-18T08:00:00+03:00',
    bitis_zamani: '2026-08-18T12:00:00+03:00',
    nokta_id: 1,
    eksik_sayi: 1,
  },
  {
    acik_id: 2,
    baslangic_zamani: '2026-08-20T08:00:00+03:00',
    bitis_zamani: '2026-08-20T14:00:00+03:00',
    nokta_id: 1,
    eksik_sayi: 1,
  },
  {
    acik_id: 3,
    baslangic_zamani: '2026-08-20T14:00:00+03:00',
    bitis_zamani: '2026-08-20T18:00:00+03:00',
    nokta_id: 2,
    eksik_sayi: 1,
  },
  {
    acik_id: 4,
    baslangic_zamani: '2026-08-22T20:00:00+03:00',
    bitis_zamani: '2026-08-22T23:00:00+03:00',
    nokta_id: 1,
    eksik_sayi: 1,
  },
]

const GUNLUK_KAPSAMA = [
  { tarih: '2026-08-17', acik_aralik_sayisi: 0, karsilanmayan_kisi_saat: 0 },
  { tarih: '2026-08-18', acik_aralik_sayisi: 1, karsilanmayan_kisi_saat: 4 },
  { tarih: '2026-08-19', acik_aralik_sayisi: 0, karsilanmayan_kisi_saat: 0 },
  { tarih: '2026-08-20', acik_aralik_sayisi: 2, karsilanmayan_kisi_saat: 10 },
  { tarih: '2026-08-21', acik_aralik_sayisi: 0, karsilanmayan_kisi_saat: 0 },
  { tarih: '2026-08-22', acik_aralik_sayisi: 1, karsilanmayan_kisi_saat: 3 },
  { tarih: '2026-08-23', acik_aralik_sayisi: 0, karsilanmayan_kisi_saat: 0 },
]

// Sekiz kişi, |sapma| çeşitli — "en çok sapan üstte, altı satırla sınırlı"
// ölçütünü sınamak için yeterli. abs sırası: B(20) H(15) G(12) A(10) C(5)
// D(5) E(1) F(1); ilk altı B,H,G,A,C,D — E ve F dışarıda kalmalı.
const SAAT_DAGILIMI = [
  { personel_id: 1, ad_soyad: 'Kişi A', toplam_saat: 160, hedef_saat: 150, sapma: 10 },
  { personel_id: 2, ad_soyad: 'Kişi B', toplam_saat: 130, hedef_saat: 150, sapma: -20 },
  { personel_id: 3, ad_soyad: 'Kişi C', toplam_saat: 155, hedef_saat: 150, sapma: 5 },
  { personel_id: 4, ad_soyad: 'Kişi D', toplam_saat: 145, hedef_saat: 150, sapma: -5 },
  { personel_id: 5, ad_soyad: 'Kişi E', toplam_saat: 151, hedef_saat: 150, sapma: 1 },
  { personel_id: 6, ad_soyad: 'Kişi F', toplam_saat: 149, hedef_saat: 150, sapma: -1 },
  { personel_id: 7, ad_soyad: 'Kişi G', toplam_saat: 138, hedef_saat: 150, sapma: -12 },
  { personel_id: 8, ad_soyad: 'Kişi H', toplam_saat: 165, hedef_saat: 150, sapma: 15 },
]

// Üç senaryo (bkz. testler):
//  1. dönemle KESİŞİR ama BUGÜNDEN ÖNCE biter (19 Ağustos) → "bu dönem
//     müsait olmayanlar"da görünür, "yaklaşan"da GÖRÜNMEZ (bugün 20'si).
//  2. dönemin dışında BAŞLAR (1 Eylül) → "bu dönem"de GÖRÜNMEZ, ama
//     bugünden sonra bittiği için "yaklaşan"da görünür.
//  3. dönemden önce biter (5 Temmuz) → ikisinde de GÖRÜNMEZ.
const MUSAITLIKLER: Musaitlik[] = [
  {
    belge_var: false,
    musaitlik_id: 1,
    personel_id: 1,
    baslangic_tarihi: '2026-08-19',
    bitis_tarihi: '2026-08-19',
    dilim: 'tam_gun',
    tip: 'yillik_izin',
    not_: null,
  },
  {
    belge_var: false,
    musaitlik_id: 2,
    personel_id: 2,
    baslangic_tarihi: '2026-09-01',
    bitis_tarihi: '2026-09-03',
    dilim: 'tam_gun',
    tip: 'rapor',
    not_: null,
  },
  {
    belge_var: false,
    musaitlik_id: 3,
    personel_id: 1,
    baslangic_tarihi: '2026-07-01',
    bitis_tarihi: '2026-07-05',
    dilim: 'tam_gun',
    tip: 'egitim',
    not_: null,
  },
]

const TERCIHLER: Tercih[] = []

function analiz(ek: Partial<Analiz> = {}): Analiz {
  return {
    surum_id: 10,
    kapsama_orani: 0.85,
    fazla_kadro: [],
    toplam_fazla_kadro: 0,
    kisi_basina_gece: [],
    kisi_basina_hafta_sonu: [],
    saat_dagilimi: SAAT_DAGILIMI as never,
    en_dengesiz_personel_id: null,
    en_dengesiz_ad_soyad: null,
    tercih_karsilama_orani: null,
    bina_degisim_sayisi: [],
    ceza_dokumu: null,
    toplam_ceza: 4200,
    ceza_kaynagi: 'cozucu',
    karsilanmayan_kisi_saat: 17,
    acik_aralik_sayisi: 4,
    gunluk_kapsama: GUNLUK_KAPSAMA as never,
    kota_durumu: [],
    yillik_kota_saat: 270,
    ceza_kalemleri: [],
    kumulatif_degisim: { onceki_surum_id: null, onceki_ortalama_sapma: null, simdiki_ortalama_sapma: null },
    ufuk: 'donem',
    ...ek,
  }
}

const SURUM_OLCULEBILIR: CizelgeSurumu = {
  surum_id: 10,
  donem_id: 1,
  surum_no: 3,
  durum: 'yayinlandi',
  onceki_surum_id: null,
  yayin_zamani: null,
  olusturma_zamani: '2026-08-16T10:00:00',
  guncelleme_zamani: '2026-08-16T10:00:00',
  damga: 'x',
  toplam_ceza: 4200,
  kapsama_acigi_sayisi: 4,
  fazla_kadro_sayisi: 0,
  atama_sayisi: 40,
}

// Modül düzeyinde taklit — yanıtlar testten teste değişebilsin diye
// değiştirilebilir değişkenlerden okunur (bkz. AnalizEkrani.test.tsx).
let _surumler: CizelgeSurumu[] = [SURUM_OLCULEBILIR]
let _analiz: Analiz = analiz()
let _kapsamaAcigi: KapsamaAcigi[] = KAPSAMA_ACIGI
let _musaitlikler: Musaitlik[] = MUSAITLIKLER

vi.mock('../api/client', () => ({
  api: {
    donemler: () => Promise.resolve([DONEM]),
    personelListele: () => Promise.resolve(PERSONEL),
    noktaListele: () => Promise.resolve(NOKTALAR),
    musaitlikListele: () => Promise.resolve(_musaitlikler),
    tercihListele: () => Promise.resolve(TERCIHLER),
    surumler: () => Promise.resolve(_surumler),
    surumKapsamaAcigi: () => Promise.resolve(_kapsamaAcigi),
    analizGetir: () => Promise.resolve(_analiz),
  },
}))

afterEach(cleanup)

function ekraniKur() {
  ciz(<OzetEkrani ekranSec={vi.fn()} />)
}

describe('Özet ekranı — aralık metni', () => {
  it('dönem seçici (combobox) YOKTUR — dönem bugünden türetilir', async () => {
    ekraniKur()
    await screen.findAllByText(/17 – 23/)
    expect(screen.queryByRole('combobox')).toBeNull()
  })

  it('her aralık-bağlı blok aralık metnini taşır', async () => {
    ekraniKur()
    // Ölçü kartları şeridi, günlük kapsama kartı, kişi başına saat kartı ve
    // "bu dönem müsait olmayanlar" kartı — dördü de aynı aralığı yazar.
    const araligi = await screen.findAllByText(/17 – 23/)
    expect(araligi.length).toBeGreaterThanOrEqual(4)
  })
})

/** Açık listesi başlığının yanındaki "N kayıt" sayacı. Sayı ekranda birden
 *  çok yerde geçiyor (ölçü kartları da sayı basıyor), o yüzden başlığın
 *  KARDEŞİNDEN okunur. */
function acikKayitSayisi(baslik: HTMLElement): number {
  const satir = baslik.parentElement as HTMLElement
  const eslesme = /(\d+)\s*kayıt/.exec(satir.textContent ?? '')
  if (!eslesme) throw new Error(`"N kayıt" bulunamadı: ${satir.textContent}`)
  return Number(eslesme[1])
}

describe('Özet ekranı — günlük kapsama şeridi', () => {
  /**
   * VARSAYILAN SÜZGEÇSİZ. Önceden liste "bugün"e süzülüydü ve dönem bugünü
   * içermek zorunda olmadığı için (donemSec bugünü içeren dönem yoksa en
   * yakın GELECEK dönemi seçer) şerit kırmızı çubuklarla dolarken hemen
   * altında "Açık kayıt yok" yazıyordu. Aynı kusurun ikinci yüzü: seçili
   * güne tekrar tıklamak süzgeci kaldırmıyor, "bugün"e döndürüyordu.
   */
  it('açılışta liste SÜZÜLMEMİŞTİR — dönemin tüm açıkları görünür', async () => {
    ekraniKur()

    // Şerit analiz yanıtıyla gelir; başlık ondan önce de basılıyor, o yüzden
    // beklenen şey ŞERİDİN KENDİSİ.
    await screen.findByRole('button', { name: /18 Ağustos/ })
    const baslik = screen.getByText('Dönemin açık kayıtları')
    // Dört açık kaydın TAMAMI: 18'inde bir, 20'sinde iki, 22'sinde bir.
    expect(acikKayitSayisi(baslik)).toBe(4)
    expect(screen.getAllByText('Nöbet Masası').length).toBe(3)
    expect(screen.getAllByText('Kapı Güvenliği').length).toBe(1)
  })

  it('bir güne tıklamak açık listesini o güne süzer, tekrar tıklamak SÜZGECİ KALDIRIR', async () => {
    ekraniKur()

    // 18 Ağustos günü düğmesine tıkla: liste o güne süzülür (tek kayıt).
    const gun18 = await screen.findByRole('button', { name: /18 Ağustos.*4 kişi-saat eksik/ })
    fireEvent.click(gun18)
    expect(gun18.getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByText(/günü açık kayıtları$/)).toBeDefined()
    expect(screen.queryByText('Kapı Güvenliği')).toBeNull()
    expect(screen.getAllByText('Nöbet Masası').length).toBe(1)

    // Aynı güne TEKRAR tıklamak süzgeci kaldırır — TÜM DÖNEM geri gelir,
    // "bugün" değil.
    fireEvent.click(gun18)
    expect(gun18.getAttribute('aria-pressed')).toBe('false')
    const baslik = screen.getByText('Dönemin açık kayıtları')
    expect(acikKayitSayisi(baslik)).toBe(4)
    expect(screen.getAllByText('Nöbet Masası').length).toBe(3)
    expect(screen.getAllByText('Kapı Güvenliği').length).toBe(1)
  })
})

describe('Özet ekranı — toplam ceza kartının kaynağı', () => {
  /**
   * İki kaynağın KAPSAMI farklı: "cozucu"da sayı amaç fonksiyonunun tamamı
   * (S8 dahil), "kurallardan"da S8 bilinçli olarak dışarıda. Kaynak
   * yazılmazsa çözülmüş bir sürümde tek vardiya kaydıran kullanıcı sayının
   * düşüşünü çizelgenin iyileşmesi sanar.
   */
  it('çözücü kaynağını yazar', async () => {
    _analiz = analiz({ ceza_kaynagi: 'cozucu' })
    ekraniKur()
    expect(await screen.findByText(/çözüm işinden/)).toBeDefined()
    _analiz = analiz()
  })

  it('kural motorundan hesaplanan dökümde S8\'in dışarıda olduğunu söyler', async () => {
    _analiz = analiz({ ceza_kaynagi: 'kurallardan' })
    ekraniKur()
    const satir = await screen.findByText(/kurallardan hesaplandı/)
    expect(satir.textContent).toContain('S8 hariç')
    // Kapsamın kaynakla birlikte değiştiği ipucunda YAZILI.
    expect(satir.getAttribute('title')).toContain('kapsamı da değişir')
    _analiz = analiz()
  })
})

describe('Özet ekranı — kişi başına saat', () => {
  it('en çok sapanı üstte verir ve altı satırla sınırlıdır', async () => {
    ekraniKur()

    await screen.findByText('Kişi B')
    // Yalnız ilk altı kişi (B,H,G,A,C,D) görünür; E ve F dışarıda kalır.
    expect(screen.queryByText('Kişi E')).toBeNull()
    expect(screen.queryByText('Kişi F')).toBeNull()
    expect(screen.getByText('Kişi H')).toBeDefined()
    expect(screen.getByText('Kişi D')).toBeDefined()
  })
})

describe('Özet ekranı — bu dönem müsait olmayanlar', () => {
  it('dönemle kesişmeyen kaydı göstermez', async () => {
    ekraniKur()

    // Başlık buyukHarf() ile büyütülür (Rozet/KartEtiketi kalıbı) — kartı
    // KART düzeyinde bulup İÇİNDE arıyoruz, çünkü "Mert Can" başka bir
    // kartta (yaklaşan müsaitlik kayıtları) da geçer.
    const baslik = await screen.findByText(/BU DÖNEM MÜSAİT OLMAYANLAR/)
    const kart = baslik.closest('[data-slot="card"]') as HTMLElement
    // Elif'in 19 Ağustos izni dönemin İÇİNDE — bu kartta görünmeli.
    expect(within(kart).getByText('Elif Aydın')).toBeDefined()
    // Mert'in 1-3 Eylül raporu dönemin DIŞINDA başlıyor — bu kartta
    // GÖRÜNMEMELİ.
    expect(within(kart).queryByText('Mert Can')).toBeNull()
  })
})

describe('Özet ekranı — atamasız taslak', () => {
  it('ölçü yerine durum metni çıkar', async () => {
    _surumler = [
      {
        ...SURUM_OLCULEBILIR,
        surum_id: 11,
        surum_no: 1,
        durum: 'taslak',
        atama_sayisi: 0,
      },
    ]
    ekraniKur()

    expect(
      await screen.findByText(
        /Bu dönemin son sürümü henüz boş bir taslak\. Çizelge ekranından elle çizebilir ya da Çözüm ekranını kullanabilirsin\./,
      ),
    ).toBeDefined()
    // Ölçü kartları (kapsama, toplam ceza, sürüm durumu) sayı yerine tire
    // gösterir.
    expect(screen.getAllByText(BOS).length).toBeGreaterThan(0)

    _surumler = [SURUM_OLCULEBILIR]
  })
})

describe('Özet ekranı — yaklaşan müsaitlik kayıtları', () => {
  it('etiket "bugünden itibaren" der', async () => {
    ekraniKur()
    // Başlık KartEtiketi içinde buyukHarf() ile büyütülür: "İ" tr-TR'de
    // noktalı büyür (U+0130), ASCII /i bayrağı onu "i" ile eşleştiremez
    // (bkz. DonemOzetimEkrani.test.tsx aynı notu taşır) — bu yüzden büyük
    // harfli tam metin, /i BAYRAKSIZ sorgulanır.
    expect(await screen.findByText(/BUGÜNDEN İTİBAREN/)).toBeDefined()
  })
})
