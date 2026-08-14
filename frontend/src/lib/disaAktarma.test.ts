import { describe, expect, it } from 'vitest'
import type {
  Atama,
  CizelgeSurumu,
  Donem,
  GorevNoktasi,
  FazlaKadro,
  KapsamaAcigi,
  Personel,
} from '@/api/types'
import {
  CSV_AYRACI,
  UTF8_BOM,
  cizelgeCsvOlustur,
  disaAktarmaDosyaAdi,
  kapsamaAcigiCsvOlustur,
  type CizelgeVerisi,
} from './disaAktarma'

const DONEM: Donem = {
  donem_id: 1,
  baslangic_tarihi: '2026-02-02',
  bitis_tarihi: '2026-03-01',
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
  kapsama_acigi_sayisi: 2,
  fazla_kadro_sayisi: 0,
}

function personel(id: number, sicil: string, ad: string): Personel {
  return {
    personel_id: id,
    ad_soyad: ad,
    sicil_no: sicil,
    haftalik_hedef_saat: 40,
    aktif_baslangic: '2026-01-01',
    aktif_bitis: null,
    yetkinlik_idleri: [],
  devir_fazla_calisma_saat: '0.00',
  kota_yili: null,
  }
}

function nokta(id: number, ad: string): GorevNoktasi {
  return { nokta_id: id, ad, bina_id: null, onkosul_yetkinlik_id: null, aktif: true }
}

// `vId` artık vardiya tipi değil BAŞLANGIÇ SAATİ; süre sekiz saat.
function atama(id: number, personelId: number, tarih: string, vId: number, nId: number): Atama {
  const bas = vId === 11 ? 0 : 8
  return {
    atama_id: id,
    personel_id: personelId,
    baslangic_zamani: `${tarih}T${String(bas).padStart(2, '0')}:00:00+03:00`,
    bitis_zamani: `${tarih}T${String((bas + 8) % 24).padStart(2, '0')}:00:00+03:00`,
    tarih,
    sure_saat: 8,
    nokta_id: nId,
    kilitli: false,
    kaynak: 'cozucu',
  }
}

function gunSonrasi(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + 1)
  return d.toISOString().slice(0, 10)
}

function acik(id: number, tarih: string, vId: number, nId: number, eksik: number): KapsamaAcigi {
  const bas = vId === 11 ? 0 : 8
  return {
    acik_id: id,
    baslangic_zamani: `${tarih}T${String(bas).padStart(2, '0')}:00:00+03:00`,
    bitis_zamani: `${bas + 8 >= 24 ? gunSonrasi(tarih) : tarih}T${String((bas + 8) % 24).padStart(2, '0')}:00:00+03:00`,
    nokta_id: nId,
    eksik_sayi: eksik,
  }
}

function fazla(id: number, tarih: string, vId: number, nId: number, sayi: number): FazlaKadro {
  const bas = vId === 11 ? 0 : 8
  return {
    fazla_id: id,
    baslangic_zamani: `${tarih}T${String(bas).padStart(2, '0')}:00:00+03:00`,
    bitis_zamani: `${bas + 8 >= 24 ? gunSonrasi(tarih) : tarih}T${String((bas + 8) % 24).padStart(2, '0')}:00:00+03:00`,
    nokta_id: nId,
    fazla_sayi: sayi,
  }
}

function veriKur(
  atamalar: Atama[],
  kapsamaAcigi: KapsamaAcigi[] = [],
  ekPersonel: Personel[] = [],
  fazlaKadro: FazlaKadro[] = [],
): CizelgeVerisi {
  return {
    donem: DONEM,
    surum: SURUM,
    atamalar,
    kapsamaAcigi,
    fazlaKadro,
    personelMap: new Map(
      [
        personel(1, 'GG-001', 'Ayşe Şahin'),
        personel(2, 'GG-002', 'Mehmet Çınar'),
        ...ekPersonel,
      ].map((p) => [p.personel_id, p]),
    ),
    noktaMap: new Map(
      [nokta(20, 'Güvenlik'), nokta(21, 'Vardiya Şefliği')].map((n) => [n.nokta_id, n]),
    ),
  }
}

/** BOM ve son satır sonu ayıklanmış veri satırları. */
function satirlar(csv: string): string[] {
  return csv.replace(UTF8_BOM, '').trimEnd().split('\r\n')
}

describe('CSV kodlama tuzakları', () => {
  const csv = cizelgeCsvOlustur(veriKur([atama(1, 1, '2026-02-02', 10, 20)]))

  it('UTF-8 BOM ile başlar', () => {
    // BOM olmadan Excel dosyayı Windows kod sayfasıyla açar ve "Güvenlik"
    // bozulur.
    expect(csv.startsWith(UTF8_BOM)).toBe(true)
    expect(UTF8_BOM).toBe('﻿')
  })

  it('ayraç noktalı virgüldür', () => {
    expect(CSV_AYRACI).toBe(';')
    expect(satirlar(csv)[0]).toContain(';')
  })

  it('hiçbir alan ayraç olarak virgül kullanmaz', () => {
    // Türkçe yerelli Excel virgülü ondalık ayracı sayar; virgül kaçarsa
    // bütün satır tek sütuna yığılır.
    for (const s of satirlar(csv)) {
      expect(s.split(';').length).toBeGreaterThan(1)
    }
  })

  it('Türkçe karakterleri olduğu gibi taşır', () => {
    expect(csv).toContain('Ayşe Şahin')
    expect(csv).toContain('Güvenlik')
  })

  it('satır sonu CRLF', () => {
    expect(csv).toContain('\r\n')
  })
})

describe('cizelgeCsvOlustur — uzun biçim', () => {
  it('satır sayısı atama sayısıyla eşleşir', () => {
    const atamalar = [
      atama(1, 1, '2026-02-02', 10, 20),
      atama(2, 2, '2026-02-02', 11, 21),
      atama(3, 1, '2026-02-03', 11, 20),
    ]
    const veri = satirlar(cizelgeCsvOlustur(veriKur(atamalar)))
    // Başlık + atama başına bir satır.
    expect(veri).toHaveLength(atamalar.length + 1)
  })

  it('atama yokken yalnızca başlık satırı kalır', () => {
    expect(satirlar(cizelgeCsvOlustur(veriKur([])))).toHaveLength(1)
  })

  it('SRS 7.2 sütunlarını taşır; iki sütun saat modeline uyarlandı', () => {
    const basliklar = satirlar(cizelgeCsvOlustur(veriKur([])))[0]!.split(';')
    for (const srs of ['sicil', 'ad', 'tarih', 'hafta_sonu_mu', 'sure_saat']) {
      expect(basliklar).toContain(srs)
    }
    // `vardiya_tipi` → `baslangic`/`bitis`: taşınacak bir tip adı yok, blok
    // bir zaman aralığı (SRS TD-13).
    expect(basliklar).toContain('baslangic')
    expect(basliklar).toContain('bitis')
    expect(basliklar).not.toContain('vardiya_tipi')
    // `gece_mi` → `gece_saat`: gece HESAPLANIR, işaretlenmez (TD-2) ve
    // ölçünün birimi saattir.
    expect(basliklar).toContain('gece_saat')
    expect(basliklar).not.toContain('gece_mi')
    expect(basliklar).toContain('gorev_noktasi')
  })

  it('bir atamanın alanlarını doğru yazar', () => {
    const csv = cizelgeCsvOlustur(veriKur([atama(1, 2, '2026-02-07', 11, 21)]))
    // 2026-02-07 cumartesi; vardiya gece.
    expect(satirlar(csv)[1]).toBe(
      // `gece_mi` bayrağı yerine GECE SAATİ (SRS TD-2): 00.00–08.00 bloğunun
      // altı saati gece penceresinde (00–06); 06 ve 07 gece değildir.
      // Başlangıç ve bitiş TAM ISO DAMGASIDIR (Tur 6): "00.00; 08.00" yazan
      // bir satır, bitişin hangi güne düştüğünü makineye söyleyemez.
      '2026-02-07;GG-002;Mehmet Çınar;2026-02-07T00:00:00+03:00;2026-02-07T08:00:00+03:00;Vardiya Şefliği;6;evet;8',
    )
  })

  it('hafta içi gündüz atamasında iki bayrak da hayır', () => {
    const csv = cizelgeCsvOlustur(veriKur([atama(1, 1, '2026-02-02', 10, 20)]))
    expect(satirlar(csv)[1]).toBe(
      '2026-02-02;GG-001;Ayşe Şahin;2026-02-02T08:00:00+03:00;2026-02-02T16:00:00+03:00;Güvenlik;0;hayir;8',
    )
  })

  it('gece yarısını aşan blokta bitiş damgası ERTESİ GÜNÜ gösterir', () => {
    // Bu satır, saat metniyle yazıldığında okunamaz olan tek durumdur:
    // "20.00; 06.00" bitişin ertesi güne düştüğünü söylemez.
    const gece = {
      ...atama(1, 1, '2026-02-02', 10, 20),
      baslangic_zamani: '2026-02-02T20:00:00+03:00',
      bitis_zamani: '2026-02-03T06:00:00+03:00',
      sure_saat: 10,
    }
    const alanlar = satirlar(cizelgeCsvOlustur(veriKur([gece])))[1]!.split(';')
    expect(alanlar[3]).toBe('2026-02-02T20:00:00+03:00')
    expect(alanlar[4]).toBe('2026-02-03T06:00:00+03:00')
  })

  it('tarihe, sonra personele göre sıralar', () => {
    const csv = cizelgeCsvOlustur(
      veriKur([
        atama(1, 2, '2026-02-03', 10, 20),
        atama(2, 1, '2026-02-03', 10, 20),
        atama(3, 1, '2026-02-02', 10, 20),
      ]),
    )
    expect(satirlar(csv).slice(1).map((s) => s.split(';').slice(0, 2).join(' '))).toEqual([
      '2026-02-02 GG-001',
      '2026-02-03 GG-001',
      '2026-02-03 GG-002',
    ])
  })

  it('tarihi ISO bırakır — okuyucu tablo programı (SRS 7.2)', () => {
    const csv = cizelgeCsvOlustur(veriKur([atama(1, 1, '2026-02-02', 10, 20)]))
    expect(satirlar(csv)[1]).toContain('2026-02-02')
    expect(csv).not.toContain('Şubat')
  })

  it('ayraç içeren adı tırnaklar', () => {
    const veri = veriKur([atama(1, 3, '2026-02-02', 10, 20)], [], [
      personel(3, 'GG-003', 'Yılmaz; Ali'),
    ])
    expect(cizelgeCsvOlustur(veri)).toContain('"Yılmaz; Ali"')
  })
})

describe('kapsamaAcigiCsvOlustur', () => {
  it('açık hücreleri çıktıya alır', () => {
    const acikSatirlari = [acik(1, '2026-02-02', 11, 20, 2), acik(2, '2026-02-05', 10, 21, 1)]
    const veri = satirlar(kapsamaAcigiCsvOlustur(veriKur([], acikSatirlari)))
    expect(veri).toHaveLength(acikSatirlari.length + 1)
    expect(veri[0]).toBe('baslangic;bitis;gorev_noktasi;tur;kisi_sayisi')
    expect(veri[1]).toBe('2026-02-02T00:00:00+03:00;2026-02-02T08:00:00+03:00;Güvenlik;eksik;2')
  })

  it('açık yokken başlık satırı kalır — sıfır satır "açık yok" demektir', () => {
    // Dosyanın sessizce hiç üretilmemesi, açıkların gösterilmediği bir
    // çıktıyla açığı olmayan bir çizelgeyi ayırt edilemez kılardı.
    const veri = satirlar(kapsamaAcigiCsvOlustur(veriKur([], [])))
    expect(veri).toHaveLength(1)
    expect(veri[0]).toBe('baslangic;bitis;gorev_noktasi;tur;kisi_sayisi')
  })

  it('açık dosyası da BOM ve noktalı virgül taşır', () => {
    const csv = kapsamaAcigiCsvOlustur(veriKur([], [acik(1, '2026-02-02', 11, 20, 2)]))
    expect(csv.startsWith(UTF8_BOM)).toBe(true)
    expect(satirlar(csv)[1]!.split(';')).toHaveLength(5)
  })

  it('tarihe göre sıralar', () => {
    const csv = kapsamaAcigiCsvOlustur(
      veriKur([], [acik(1, '2026-02-09', 10, 20, 1), acik(2, '2026-02-02', 10, 20, 1)]),
    )
    // Sıralama artık DAMGAYA göre; günü damganın tarih bölümü verir.
    expect(satirlar(csv).slice(1).map((s) => s.split(';')[0]!.slice(0, 10))).toEqual([
      '2026-02-02',
      '2026-02-09',
    ])
  })
})

describe('disaAktarmaDosyaAdi', () => {
  it('dönem ve sürümü taşır', () => {
    expect(disaAktarmaDosyaAdi(DONEM, SURUM, 'cizelge')).toBe(
      'cizelge_2026-02-02_2026-03-01_surum3.csv',
    )
  })

  it('kapsama açığı dosyası ayrı adla iner', () => {
    expect(disaAktarmaDosyaAdi(DONEM, SURUM, 'kapsama-acigi')).toBe(
      'kapsama-acigi_2026-02-02_2026-03-01_surum3.csv',
    )
  })

  it('iki dosya adı birbirinden ayrılır', () => {
    expect(disaAktarmaDosyaAdi(DONEM, SURUM, 'cizelge')).not.toBe(
      disaAktarmaDosyaAdi(DONEM, SURUM, 'kapsama-acigi'),
    )
  })
})

describe('talep sapması dosyası — iki yön tek dosyada', () => {
  /**
   * SRS 7.2 kapsama açığını AYRI bir dosyaya koyar; gerekçesi iki farklı
   * SATIR ŞEKLİNİN tek dosyada birleşmesidir. Fazla kadronun şekli açıkla
   * AYNI olduğundan (aynı dört anahtar, aynı sayı) o gerekçe burada
   * geçerli değil; `tur` sütunu ayrımı yapar.
   */
  it('eksik ve fazla satırları aynı dosyada, tür sütunuyla ayrışır', () => {
    const csv = kapsamaAcigiCsvOlustur(
      veriKur([], [acik(1, '2026-02-02', 11, 20, 2)], [], [fazla(1, '2026-02-03', 10, 21, 1)]),
    )
    const veri = satirlar(csv)
    expect(veri[0]).toBe('baslangic;bitis;gorev_noktasi;tur;kisi_sayisi')
    expect(veri).toContain('2026-02-02T00:00:00+03:00;2026-02-02T08:00:00+03:00;Güvenlik;eksik;2')
    expect(veri).toContain('2026-02-03T08:00:00+03:00;2026-02-03T16:00:00+03:00;Vardiya Şefliği;fazla;1')
  })

  it('kişi sayısı her iki yönde de POZİTİF kalır', () => {
    // "eksik_sayi = 2, tur = fazla" okunamayan bir satır olurdu; sütun adı
    // yönü değil büyüklüğü taşır, yönü `tur` söyler.
    const csv = kapsamaAcigiCsvOlustur(veriKur([], [], [], [fazla(1, '2026-02-02', 11, 20, 3)]))
    expect(satirlar(csv)[1]).toBe('2026-02-02T00:00:00+03:00;2026-02-02T08:00:00+03:00;Güvenlik;fazla;3')
  })

  it('yalnızca fazla kadro varken de dosya üretilir', () => {
    const veri = satirlar(
      kapsamaAcigiCsvOlustur(veriKur([], [], [], [fazla(1, '2026-02-02', 11, 20, 1)])),
    )
    expect(veri).toHaveLength(2)
  })

  it('iki yön birlikte tarihe göre sıralanır', () => {
    const csv = kapsamaAcigiCsvOlustur(
      veriKur(
        [],
        [acik(1, '2026-02-10', 11, 20, 1)],
        [],
        [fazla(1, '2026-02-03', 10, 20, 1), fazla(2, '2026-02-20', 10, 20, 1)],
      ),
    )
    const tarihler = satirlar(csv)
      .slice(1)
      .map((s) => s.split(';')[0]!.slice(0, 10))
    expect(tarihler).toEqual(['2026-02-03', '2026-02-10', '2026-02-20'])
  })
})
