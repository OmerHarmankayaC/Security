import { cleanup, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Atama, CizelgeSurumu, Donem, GorevNoktasi, Personel } from '@/api/types'
import type { CizelgeVerisi } from '@/lib/disaAktarma'
import { YazdirmaOnizlemesi } from './YazdirmaOnizlemesi'
import { ciz } from '@/test/ciz'

afterEach(cleanup)

/**
 * Yazdırma önizlemesinin YERLEŞİMİ (Tur 7 İş 5).
 *
 * Hata "yalnızca ilk gün basılıyor" diye bildirildi ama nedeni bileşende
 * değildi: önizleme `position: fixed` + `overflow: auto` bir kabın içinde
 * duruyor, baskı CSS'i de yazdırma alanına `position: absolute` veriyordu.
 * Akış dışına çıkan içerik sayfalanmaz.
 *
 * jsdom sayfalama yapmaz, dolayısıyla "yedi sayfa çıktı mı" TEST EDİLEMEZ.
 * Test edilebilen ve hatanın gerçek nedeni olan şey YERLEŞİMDİR: önizleme
 * `#root`un içinde değil KARDEŞİ olmalı, çünkü baskı CSS'i `#root`u
 * tümüyle gizleyerek çalışıyor. Bu bozulursa çıktı sessizce tek sayfaya
 * düşer ve kimse fark etmez.
 */

const DONEM: Donem = {
  donem_id: 1,
  baslangic_tarihi: '2026-02-02',
  bitis_tarihi: '2026-02-08',
  tercih_son_tarihi: '2026-01-26',
}

const SURUM: CizelgeSurumu = {
  surum_id: 9,
  donem_id: 1,
  surum_no: 3,
  durum: 'cozuldu',
  onceki_surum_id: null,
  yayin_zamani: null,
  olusturma_zamani: '2026-02-01T09:00:00Z',
  guncelleme_zamani: '2026-02-01T09:00:00Z',
  damga: 'd1',
  toplam_ceza: 912,
  kapsama_acigi_sayisi: 0,
  fazla_kadro_sayisi: 0,
  // Gorev 6/7: sozlesmeye eklendi, bu testler onu okumaz.
  atama_sayisi: 20,
}

const PERSONEL: Personel = {
  personel_id: 1,
  ad_soyad: 'Ayşe Şahin',
  sicil_no: 'GG-001',
  haftalik_hedef_saat: 40,
  aktif_baslangic: '2026-01-01',
  aktif_bitis: null,
  yetkinlik_idleri: [],
  devir_fazla_calisma_saat: '0.00',
  kota_yili: null,
}

const NOKTA: GorevNoktasi = {
  nokta_id: 20,
  ad: 'Güvenlik',
  bina_id: null,
  onkosul_yetkinlik_id: null,
  aktif: true,
}

const ATAMA: Atama = {
  atama_id: 1,
  personel_id: 1,
  baslangic_zamani: '2026-02-02T08:00:00+03:00',
  bitis_zamani: '2026-02-02T16:00:00+03:00',
  tarih: '2026-02-02',
  sure_saat: 8,
  nokta_id: 20,
  kilitli: false,
  kaynak: 'cozucu',
}

const VERI: CizelgeVerisi = {
  donem: DONEM,
  surum: SURUM,
  atamalar: [ATAMA],
  kapsamaAcigi: [],
  fazlaKadro: [],
  personelMap: new Map([[1, PERSONEL]]),
  noktaMap: new Map([[20, NOKTA]]),
}

describe('önizleme GÖVDEYE bağlanır — baskı CSS i buna dayanıyor', () => {
  it('uygulama kabının içinde DEĞİL, gövdenin doğrudan çocuğudur', () => {
    // `render` kendi kabını gövdeye ekler; portal olmasaydı önizleme o
    // kabın İÇİNDE kalırdı. Baskıda `#root` gizlendiği için, içeride kalan
    // bir önizleme hiç basılmazdı.
    const { container } = ciz(<YazdirmaOnizlemesi veri={VERI} onKapat={vi.fn()} />)
    const kok = document.querySelector('.yazdirma-kok')
    expect(kok).not.toBeNull()
    expect(kok!.parentElement).toBe(document.body)
    expect(container.querySelector('.yazdirma-kok')).toBeNull()
  })

  it('baskı CSS inin tutunduğu iki sınıfı da taşır', () => {
    ciz(<YazdirmaOnizlemesi veri={VERI} onKapat={vi.fn()} />)
    // `.yazdirma-kok` katmanı akışa geri döndürür, `.yazdirma-alani`
    // basılacak içeriğin kendisidir.
    expect(document.querySelector('.yazdirma-kok .yazdirma-alani')).not.toBeNull()
  })

  it('dönemin BÜTÜN günlerini çizer — seçili günü değil', () => {
    ciz(<YazdirmaOnizlemesi veri={VERI} onKapat={vi.fn()} />)
    // Yedi günlük dönem, tek atama. Atamasız günler de basılır: kâğıda
    // bakan kişi o günün boş olduğunu ancak sayfayı görürse bilir.
    expect(document.querySelectorAll('.yazdirma-tablo')).toHaveLength(7)
    expect(document.querySelectorAll('.yazdirma-sayfa-basi').length).toBeGreaterThanOrEqual(6)
  })

  it('ekran düğmeleri baskıda gizlenecek sınıfı taşır', () => {
    ciz(<YazdirmaOnizlemesi veri={VERI} onKapat={vi.fn()} />)
    const gizli = document.querySelector('.yazdirma-gizle')
    expect(gizli).not.toBeNull()
    expect(screen.getByRole('button', { name: 'Yazdır' })).toBeTruthy()
    expect(gizli!.contains(screen.getByRole('button', { name: 'Yazdır' }))).toBe(true)
  })
})
