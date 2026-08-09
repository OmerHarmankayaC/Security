import { describe, expect, it } from 'vitest'
import {
  donemAraligiBicimle,
  gunKisaltmasiVeNumarasi,
  haftaSonuMu,
  tarihBicimle,
  tarihUzunBicim,
  zamanBicimle,
} from './tarih'

/**
 * Arayüzdeki tarih biçimleri (madde 5). Türkçe biçim tek kaynaktan gelir;
 * ISO (YYYY-AA-GG) yalnızca API ve CSV çıktısında kalır.
 */
describe('tarihBicimle', () => {
  it('"9 Ağustos 2026" biçiminde yazar', () => {
    expect(tarihBicimle('2026-08-09')).toBe('9 Ağustos 2026')
  })

  it('gün başına sıfır eklemez', () => {
    expect(tarihBicimle('2026-02-03')).toBe('3 Şubat 2026')
  })

  it('ay adlarını Türkçe verir', () => {
    expect(tarihBicimle('2026-01-01')).toBe('1 Ocak 2026')
    expect(tarihBicimle('2026-12-31')).toBe('31 Aralık 2026')
  })
})

describe('donemAraligiBicimle', () => {
  it('aynı ay içindeki aralığı tek ay adıyla yazar', () => {
    expect(donemAraligiBicimle('2026-08-03', '2026-08-09')).toBe('03 – 09 Ağu 2026')
  })

  it('ayraç olarak en tire kullanır, kısa tire değil', () => {
    expect(donemAraligiBicimle('2026-08-03', '2026-08-09')).toContain('–')
    expect(donemAraligiBicimle('2026-08-03', '2026-08-09')).not.toContain(' - ')
  })

  it('ay değişen aralıkta her iki uca ay adı koyar', () => {
    expect(donemAraligiBicimle('2026-07-27', '2026-08-23')).toBe('27 Tem – 23 Ağu 2026')
  })

  it('yıl değişen aralıkta da tek yıl gösterir (bitiş yılı)', () => {
    expect(donemAraligiBicimle('2026-12-28', '2027-01-03')).toBe('28 Ara – 03 Oca 2027')
  })
})

describe('bağlama özgü biçimler', () => {
  it('ızgara sütun başlığı kısa kalır — yıl taşımaz', () => {
    // 2026-08-03 pazartesi. Izgarada 28 sütun yan yana durduğundan başlık
    // kısa olmak zorunda; tam tarih biçimi burada kullanılamaz.
    expect(gunKisaltmasiVeNumarasi('2026-08-03')).toBe('PZT 3')
  })

  it('çalışan panelinde gün adı belirleyicidir', () => {
    expect(tarihUzunBicim('2026-08-03')).toBe('03 Ağustos Pazartesi')
  })
})

describe('haftaSonuMu', () => {
  it('cumartesi ve pazarı hafta sonu sayar (SRS TD-3)', () => {
    expect(haftaSonuMu('2026-08-08')).toBe(true) // cumartesi
    expect(haftaSonuMu('2026-08-09')).toBe(true) // pazar
  })

  it('hafta içi günleri hafta sonu saymaz', () => {
    for (const gun of ['2026-08-03', '2026-08-04', '2026-08-05', '2026-08-06', '2026-08-07']) {
      expect(haftaSonuMu(gun), gun).toBe(false)
    }
  })
})

describe('zamanBicimle', () => {
  it('tarihi tam biçimde, saati yanında yazar', () => {
    // Girdi UTC; çıktı yerel saat. Saat kısmı ortama bağlı olduğundan
    // yalnızca yapı doğrulanır: "<gün> <Ay> <yıl> SS:DD".
    expect(zamanBicimle('2026-08-09T11:20:00Z')).toMatch(
      /^\d{1,2} [A-Za-zÇĞİÖŞÜçğıöşü]+ \d{4} \d{2}:\d{2}$/,
    )
  })

  it('sayısal gün.ay biçimi üretmez', () => {
    expect(zamanBicimle('2026-08-09T11:20:00Z')).not.toMatch(/\d{2}\.\d{2}/)
  })
})
