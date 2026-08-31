/**
 * Dönem Özetim ekranı (SDD 6.1, FR-9.5).
 *
 * BU TESTLER GÖRSEL DOĞRULAMANIN YERİNE GEÇMEZ; ölçülen şey davranış —
 * hangi ufkun çekildiği, kıyasın hangi sayıya göre yapıldığı, havuz dışı
 * metinlerin ne dediği.
 */
import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { DonemOzeti, Vardiyalarim } from '@/api/types'

import { DonemOzetimEkrani } from './DonemOzetimEkrani'
import { ciz } from '@/test/ciz'

let _ozet: DonemOzeti | null
// Varsayılan davranış senkron gibi çözülür (`_ozet`). Yarış/hata senaryolarını
// sınamak isteyen testler `_yavas`ı `true` yapıp yanıtı ELİNDE tutar — gerçek
// `fetch` gibi, çağrı anında değil test kararıyla çözülür/reddedilir. `_hata`
// ayarlıysa (ve `_yavas` değilse) istek doğrudan reddedilir. Diğer testler
// bundan etkilenmez.
let _yavas = false
let _hata: Error | null = null
let _bekleyenler: Array<{ resolve: (v: DonemOzeti | null) => void; reject: (e: unknown) => void }> = []
const calisanOzetim = vi.fn()

vi.mock('@/api/client', () => ({
  // `ApiHatasi` DA verilmeli: `hataMetni` sunucu kodunu okumak için ona
  // bakıyor ve taklit onu atlarsa `instanceof` yükselir.
  ApiHatasi: class ApiHatasi extends Error {},
  api: {
    calisanOzetim: (...a: unknown[]) => {
      calisanOzetim(...a)
      if (_yavas) {
        return new Promise<DonemOzeti | null>((resolve, reject) => _bekleyenler.push({ resolve, reject }))
      }
      if (_hata) return Promise.reject(_hata)
      return Promise.resolve(_ozet)
    },
  },
}))

const VERI = {
  donem_baslangic_tarihi: '2026-08-17',
  donem_bitis_tarihi: '2026-08-23',
} as Vardiyalarim

const OZET: DonemOzeti = {
  ufuk: 'donem',
  gece_saati: 24,
  ekip_ortalama_gece: 20,
  adil_pay_gece: 16,
  gece_havuzunda: true,
  hafta_sonu_saati: 8,
  ekip_ortalama_hafta_sonu: 8,
  adil_pay_hafta_sonu: 8,
  hafta_sonu_havuzunda: true,
  toplam_saat: 160,
  ekip_ortalama_saat: 158,
  hedef_saat: 160,
}

afterEach(() => {
  cleanup()
  calisanOzetim.mockClear()
  _yavas = false
  _hata = null
  _bekleyenler = []
})

describe('DonemOzetimEkrani', () => {
  it('açılışta dönem ufkunu çeker', async () => {
    _ozet = OZET
    ciz(<DonemOzetimEkrani veri={VERI} />)
    await waitFor(() => expect(calisanOzetim).toHaveBeenCalledWith('donem'))
  })

  it('ufuk değişince adalet ufkunu çeker', async () => {
    _ozet = OZET
    ciz(<DonemOzetimEkrani veri={VERI} />)
    await screen.findByText(/Gece Saati/i)
    fireEvent.click(screen.getByRole('button', { name: /90 gün/i }))
    await waitFor(() => expect(calisanOzetim).toHaveBeenCalledWith('adalet'))
  })

  it('kıyası adil paya göre kurar, ekip ortalamasına göre değil', async () => {
    // gece: sen 24, adil pay 16 -> 8 saat ÜSTÜNDE. Ekip ortalaması 20 olsaydı
    // fark 4 saat olurdu; hangi referansın kullanıldığı metinden okunur.
    _ozet = OZET
    ciz(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/8,0 saat üzerindesin/)).toBeTruthy()
  })

  it('rozet metni adil payı referans alır, "ortalama" değil', async () => {
    // Bulgu 2: fark = sen - referans (adil pay) üzerinden hesaplanır ama
    // eski rozet metni "Ortalamanın Üstünde/Altında" yazıyordu — barın
    // ADİL PAY etiketiyle ve cümledeki "adil payının ... üzerindesin"
    // ifadesiyle çelişiyordu. Rozet artık aynı referansı adlandırmalı.
    //
    // Rozet metni Rozet bileşeninde buyukHarf() ile TÜRKÇE yerelinde
    // büyütülür: "Adil" -> "ADİL" (noktalı büyük İ). JS'in case-insensitive
    // regex katlaması bunu ASCII "i" ile eşleştiremez (bkz. proje kuralı) —
    // bu yüzden büyük harfli tam metin, /i BAYRAKSIZ sorgulanır.
    _ozet = OZET
    ciz(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText('ADİL PAYIN ÜSTÜNDE')).toBeTruthy()
    expect(screen.queryByText(/Ortalaman/i)).toBeNull()
  })

  it('rozet ekip ortalamasının altındayken de "altında" değil "adil payın altında" der', async () => {
    // gece: sen 24, ekip ortalaması 30 -> ekip ortalamasına göre ALTINDA;
    // ama adil pay 16 -> referansa göre ÜSTÜNDE. Eski metin "Ortalamanın
    // Üstünde" derken hemen altındaki "ekip ortalaması 30,0 sa" satırı
    // employee'nin ekip ortalamasının altında olduğunu gösterip
    // birbirleriyle çelişirdi (final review bulgu 2, tam bu senaryo).
    _ozet = { ...OZET, gece_saati: 24, adil_pay_gece: 16, ekip_ortalama_gece: 30 }
    ciz(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText('ADİL PAYIN ÜSTÜNDE')).toBeTruthy()
  })

  it('eşik göreli: adil payın %5 altındaki fark sapma sayılmaz', async () => {
    // toplam: sen 160, hedef 160 -> fark 0. Hafta sonu 8 vs 8 -> fark 0.
    // gece payı 100, sen 103 -> fark 3 < 5 (100 * %5) -> "yakınsın".
    _ozet = { ...OZET, gece_saati: 103, adil_pay_gece: 100 }
    ciz(<DonemOzetimEkrani veri={VERI} />)
    // Referans artık ekip ortalaması değil adil pay — metin de öyle demeli.
    expect(await screen.findByText(/gece saatinde adil payına yakınsın/)).toBeTruthy()
  })

  it('adalet ufkunda toplam saat de doksan günü kapsar', async () => {
    // Bir zamanlar `toplam_saat` ufuktan habersizdi: hedef doksan günü,
    // yük yedi günü kapsıyordu ve herkes hedefinin ~160 saat altında
    // görünüyordu (ölçüldü: 52,0 karşısında 212,4). Ekran bunu "bu sayı
    // dönem içidir" uyarısıyla örtüyordu. Kaynak düzeltildi
    // (analiz_servisi + s4_hedef_paylari ufku izliyor), örtü kalktı: kartın
    // artık hiçbir istisna metni taşımaması GEREKİR, yoksa doğru sayının
    // üstüne yanlış bir uyarı basmış oluruz.
    _ozet = { ...OZET, ufuk: 'adalet', toplam_saat: 480, hedef_saat: 460 }
    ciz(<DonemOzetimEkrani veri={VERI} />)
    await screen.findByText('SON 90 GÜN')
    expect(screen.queryByText(/DÖNEM İÇİNİ kapsar/)).toBeNull()
    expect(screen.queryByText(/90 günü değil/)).toBeNull()
    // Sayı olduğu gibi, istisnasız gösterilir. (480,0 hem büyük sayıda hem
    // bar satırında geçtiği için tekil sorgu belirsiz kalır.)
    expect(screen.getAllByText(/480,0/).length).toBeGreaterThan(0)
  })

  it('özet yoksa çizelge olmadığını söyler', async () => {
    _ozet = null
    ciz(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText(/henüz yayınlanmış bir çizelge yok/i)).toBeTruthy()
  })

  it('havuz dışındaki karşılaştırmayı hiç göstermez', async () => {
    _ozet = { ...OZET, gece_havuzunda: false, adil_pay_gece: null }
    ciz(<DonemOzetimEkrani veri={VERI} />)
    await screen.findByText(/Hafta Sonu/i)
    expect(screen.queryByText(/Gece Saati/i)).toBeNull()
    expect(screen.getByText(/gece vardiyası bulunmadığı için/i)).toBeTruthy()
  })

  it('ufuk değişince yeni yanıt gelene kadar başlık ESKİ ufku gösterir, düğmenin seçtiğini değil', async () => {
    // SDD 6.3.4: "Son 90 Gün" yazan bir başlığın altında dönem-içi sayıları
    // göstermek, hiçbir başlık göstermemekten daha kötü — yanlış bir
    // kesinlik verir. Etiket EKRANDAKİ SAYININ ufkunu (ozet.ufuk) yazmalı,
    // düğmenin hangi ufku istediğini değil.
    _yavas = true
    ciz(<DonemOzetimEkrani veri={VERI} />)
    await waitFor(() => expect(_bekleyenler).toHaveLength(1))
    _bekleyenler.shift()!.resolve(OZET) // ilk (dönem) yanıtı gelir
    await screen.findByText(/DÖNEMİ/)

    fireEvent.click(screen.getByRole('button', { name: /90 gün/i }))
    await waitFor(() => expect(_bekleyenler).toHaveLength(1))

    // Düğme YENİ seçimi anında gösterir (ne istedim)...
    expect(screen.getByRole('button', { name: /90 gün/i }).getAttribute('aria-pressed')).toBe('true')
    // ...ama ikinci yanıt gelmeden başlık hâlâ dönem etiketini yazar, "SON
    // 90 GÜN" değil (ne görüyorum) — ekrandaki kartlar hâlâ dönem sayıları.
    expect(screen.queryByText('SON 90 GÜN')).toBeNull()
    expect(screen.getByText(/DÖNEMİ/)).toBeTruthy()

    _bekleyenler.shift()!.resolve({ ...OZET, ufuk: 'adalet' }) // ikinci (adalet) yanıtı gelir
    await waitFor(() => expect(screen.getByText('SON 90 GÜN')).toBeTruthy())
  })

  it('istek reddedilirse hata görünür, "çizelge yok" metni DEĞİL', async () => {
    // Ağ hatası / 500 / düşmüş oturum, meşru "yayınlanmış çizelge yok"
    // yanıtıyla (`null`) KARIŞTIRILMAZ — biri sunucu sorunu, biri normal hâl.
    _hata = new Error('Sunucuya ulaşılamadı')
    ciz(<DonemOzetimEkrani veri={VERI} />)
    expect(await screen.findByText('Sunucuya ulaşılamadı')).toBeTruthy()
    expect(screen.queryByText(/henüz yayınlanmış bir çizelge yok/i)).toBeNull()
  })

  it('ters sırada çözülen isteklerde ekranda son seçimin verisi kalır, bayat yanıt yazmaz', async () => {
    // "Bu Dönem" -> "Son 90 Gün" hızlı tıklanır; İKİ istek de havada kalır.
    // Önce YENİ (adalet) isteğin yanıtı gelir, SONRA eski (dönem) isteğin
    // GEÇ gelen yanıtı gelir. Yarış koruması olmadan bu, ekranı son atılan
    // isteğin üstüne eski veriyle yazardı — düğme "Son 90 Gün" basılı
    // görünürken kartlar dönem sayılarına dönerdi.
    _yavas = true
    ciz(<DonemOzetimEkrani veri={VERI} />)
    await waitFor(() => expect(_bekleyenler).toHaveLength(1))
    const donemIstegi = _bekleyenler[0]!

    fireEvent.click(screen.getByRole('button', { name: /90 gün/i }))
    await waitFor(() => expect(_bekleyenler).toHaveLength(2))
    const adaletIstegi = _bekleyenler[1]!

    // Ters sıra: önce ikinci (adalet) istek çözülür.
    adaletIstegi.resolve({ ...OZET, ufuk: 'adalet', toplam_saat: 999 })
    await waitFor(() => expect(screen.getByText('SON 90 GÜN')).toBeTruthy())

    // ...sonra ilk (dönem) isteğin bayat yanıtı GEÇ gelir.
    donemIstegi.resolve(OZET)

    // Ekranda hâlâ adalet verisi durmalı — bayat dönem yanıtı yok sayılmalı.
    // (999,0 birden fazla yerde basılır — büyük rakam ve SEN çubuğu — bu
    // yüzden tekil değil çoğul sorgu.)
    await waitFor(() => expect(screen.getAllByText('999,0').length).toBeGreaterThan(0))
    expect(screen.queryByText('17 – 23 Ağu 2026 DÖNEMİ')).toBeNull()
  })
})
