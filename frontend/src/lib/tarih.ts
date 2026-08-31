import { etkinDil } from '@/i18n/etkinDil'
import { buyukHarf } from './metin'
import type { Dil } from '@/i18n/diller'
/**
 * Arayüzdeki BÜTÜN tarih ve saat biçimlemesinin tek kaynağı.
 *
 * Kural: hiçbir ekran `new Date(...)`, `toLocaleDateString` veya elle dize
 * birleştirme ile tarih üretmez; hepsi buradan geçer. `tarih.guard.test.ts`
 * bunu kaynak dosyaları tarayarak doğrular — kural bir yorum değil, testtir.
 *
 * Biçimler:
 *   tarihBicimle              "9 Ağustos 2026"      tekil tarih, genel kullanım
 *   donemAraligiBicimle       "03 – 09 Ağu 2026"    dönem aralığı
 *   gunKisaltmasiVeNumarasi   "PZT 3"               çizelge ızgarası sütun başlığı
 *   tarihUzunBicim            "03 Ağustos Pazartesi" çalışan paneli, gün adı belirleyici
 *   zamanBicimle              "9 Ağustos 2026 14:20" tarih + saat
 *   goreliZaman               "bugün 14:20"          aynı gün üretilen kayıtlar
 *
 * Son dördü tekil tarihin kısaltılmış biçimleri değil, ayrı bağlamların
 * gerektirdiği ayrı bilgilerdir (sütun başlığında yıl yeri yok; çalışan
 * panelinde gün adı tarihten daha ayırt edici). Hepsi aynı ay/gün adı
 * tablolarını kullanır, yani biçimleme yolu tektir.
 *
 * ISO (YYYY-AA-GG) yalnızca iki yerde kalır ve bu BİLİNÇLİ bir ayrımdır:
 * (1) API ile veri alışverişi, (2) CSV dışa aktarma. CSV'nin okuyucusu insan
 * değil bir tablo programıdır ve SRS 7.2 bu dosya için ISO 8601 şart koşar;
 * makine okunur çıktıyı yerelleştirmek onu bozar.
 */
// GÜN VE AY ADLARI, iki dilde.
//
// `Intl.DateTimeFormat` KULLANILMIYOR ve bu bilinçli: tasarım kısaltmaların
// tam olarak üç harf olmasını istiyor ("PZT", "MON") ve `Intl` yerelden
// yerele değişen uzunluklar döndürüyor (İngilizce'de "Mon", Türkçe'de
// "Pzt" ama bazı ortamlarda "Pt"). Izgara sütun genişliği bu üç harfe
// göre kurulu; değişken uzunluk hizayı bozardı.
const GUN_KISALTMALARI: Record<Dil, string[]> = {
  tr: ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt'],
  en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
}

const GUN_TAM_ADLARI: Record<Dil, string[]> = {
  tr: ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'],
  en: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
}

const AY_TAM_ADLARI: Record<Dil, string[]> = {
  tr: [
    'Ocak',
    'Şubat',
    'Mart',
    'Nisan',
    'Mayıs',
    'Haziran',
    'Temmuz',
    'Ağustos',
    'Eylül',
    'Ekim',
    'Kasım',
    'Aralık',
  ],
  en: [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ],
}

const AY_KISALTMALARI: Record<Dil, string[]> = {
  tr: ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'],
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
}

/** Göreli gün etiketleri; sayıya bağlı olanlar fonksiyon. */
const GORELI: Record<Dil, { bugun: string; yarin: string; dun: string; gunOnce: (n: number) => string }> = {
  tr: {
    bugun: 'Bugün',
    yarin: 'Yarın',
    dun: 'dün',
    gunOnce: (n) => `${n} gün önce`,
  },
  en: {
    bugun: 'Today',
    yarin: 'Tomorrow',
    dun: 'yesterday',
    gunOnce: (n) => (n === 1 ? '1 day ago' : `${n} days ago`),
  },
}

const BUGUN_KUCUK: Record<Dil, string> = { tr: 'bugün', en: 'today' }

export function isoAyristir(iso: string): Date {
  return new Date(`${iso}T00:00:00`)
}

// Yerel saate göre bugünün ISO tarihi. `new Date().toISOString().slice(0, 10)`
// KULLANILMAZ: o UTC'ye göre keser ve Türkiye'de (UTC+3) gece yarısı ile 03:00
// arasında bir önceki günü verir — "bugün" kıyaslamaları o üç saat boyunca
// sessizce yanlış olur.
export function bugunIso(): string {
  return isoBicimle(new Date())
}

export function isoBicimle(tarih: Date): string {
  const yil = tarih.getFullYear()
  const ay = String(tarih.getMonth() + 1).padStart(2, '0')
  const gun = String(tarih.getDate()).padStart(2, '0')
  return `${yil}-${ay}-${gun}`
}

export function gunlerListesi(baslangicIso: string, bitisIso: string): string[] {
  const baslangic = isoAyristir(baslangicIso)
  const bitis = isoAyristir(bitisIso)
  const gunler: string[] = []
  for (let g = new Date(baslangic); g <= bitis; g.setDate(g.getDate() + 1)) {
    gunler.push(isoBicimle(g))
  }
  return gunler
}

// "9 Ağustos 2026" — tekil tarihin genel biçimi. Gün başında sıfır yoktur;
// aralık biçiminden (iki ucun hizalanması için sıfırlı) bilinçli olarak ayrılır.
export function tarihBicimle(iso: string): string {
  const d = etkinDil()
  const tarih = isoAyristir(iso)
  return `${tarih.getDate()} ${AY_TAM_ADLARI[d][tarih.getMonth()]} ${tarih.getFullYear()}`
}

// "03 – 09 Ağu 2026" (Dönem bloğu, Sayfa İskeleti — Yan menü). Ayrı ay/yıl
// gerektiren nadir durumlarda her iki uca ay adı eklenir. Ayraç en tiredir
// (–), kısa tire değil: iki tarih arasındaki aralığın tipografik karşılığı.
export function donemAraligiBicimle(baslangicIso: string, bitisIso: string): string {
  const d = etkinDil()
  const b = isoAyristir(baslangicIso)
  const s = isoAyristir(bitisIso)
  const bGun = String(b.getDate()).padStart(2, '0')
  const sGun = String(s.getDate()).padStart(2, '0')
  const sAy = AY_KISALTMALARI[d][s.getMonth()]
  if (b.getFullYear() === s.getFullYear() && b.getMonth() === s.getMonth()) {
    return `${bGun} – ${sGun} ${sAy} ${s.getFullYear()}`
  }
  const bAy = AY_KISALTMALARI[d][b.getMonth()]
  return `${bGun} ${bAy} – ${sGun} ${sAy} ${s.getFullYear()}`
}

// SRS TD-3: hafta sonu cumartesi ve pazardır. Resmî tatiller ayrı bir tanım
// varlığıdır (ozel_gun) ve burada hesaba katılmaz — bu yardımcı yalnızca
// takvimsel hafta sonunu bilir.
export function haftaSonuMu(iso: string): boolean {
  const gun = isoAyristir(iso).getDay()
  return gun === 0 || gun === 6
}

export function gunKisaltmasiVeNumarasi(iso: string): string {
  const { kisaltma, numara } = gunBasligiParcalari(iso)
  return `${kisaltma} ${numara}`
}

/**
 * Aynı başlığın PARÇALI hâli — Çizelge ızgarasının gün sütunu bunu iki
 * satıra yayar ve yalnızca numarayı "bugün" dairesinin içine alır.
 *
 * Birleşik dizeyi ekranda ikiye bölmek yerine ayrı bir biçimleyici var,
 * çünkü bölme işi `split(' ')` ile ekrana taşınsaydı gün adı boşluk içeren
 * bir yerelde sessizce yanlış parçalanırdı. Büyütme Türkçe yereliyle
 * yapılır — düz `toUpperCase` "i" harfini noktasız "I" yapar.
 */
export function gunBasligiParcalari(iso: string): { kisaltma: string; numara: string } {
  const d = etkinDil()
  const tarih = isoAyristir(iso)
  return {
    // Büyütme ETKİN DİLİN yereliyle: Türkçe'de düz `toUpperCase` "i" harfini
    // noktasız "I" yapar, İngilizce'de ise tersi olur ve "Fri" → "FRİ" çıkardı.
    kisaltma: buyukHarf(GUN_KISALTMALARI[d][tarih.getDay()]!, d),
    numara: String(tarih.getDate()),
  }
}

// Çalışan Paneli — Vardiyalarım (SDD 6.1): "03 Ağustos Pazartesi".
export function tarihUzunBicim(iso: string): string {
  const d = etkinDil()
  const tarih = isoAyristir(iso)
  const gun = String(tarih.getDate()).padStart(2, '0')
  const ay = AY_TAM_ADLARI[d][tarih.getMonth()]
  const gunAdi = GUN_TAM_ADLARI[d][tarih.getDay()]
  // Sıra dile göre: Türkçe "03 Ağustos Pazartesi", İngilizce'de gün adı
  // öne geçer ("Monday 03 August"). Aynı şablonu iki dile dayatmak, birinde
  // doğru diğerinde tuhaf okunan bir cümle üretirdi.
  return d === 'tr' ? `${gun} ${ay} ${gunAdi}` : `${gunAdi} ${gun} ${ay}`
}

// "Bugün" / "Yarın" / tam gün adı ("Çarşamba") — Vardiyalarım listesi ve
// sıradaki vardiya kartı bugunIso'ya göre kıyaslar.
export function gunEtiketi(iso: string, bugunIso: string): string {
  const d = etkinDil()
  if (iso === bugunIso) return GORELI[d].bugun
  const yarin = new Date(isoAyristir(bugunIso))
  yarin.setDate(yarin.getDate() + 1)
  if (iso === isoBicimle(yarin)) return GORELI[d].yarin
  return GUN_TAM_ADLARI[d][isoAyristir(iso).getDay()] ?? ''
}

// ISO tarihe gün ekler (negatif değer geriye gider).
export function gunEkle(iso: string, gun: number): string {
  const tarih = isoAyristir(iso)
  tarih.setDate(tarih.getDate() + gun)
  return isoBicimle(tarih)
}

// İki ISO tarih arasındaki tam gün farkı (b - a), negatif olabilir.
export function gunFarki(aIso: string, bIso: string): number {
  const MS_GUN = 86_400_000
  return Math.round((isoAyristir(bIso).getTime() - isoAyristir(aIso).getTime()) / MS_GUN)
}

// Backend zaman damgalarini (olusturma/guncelleme/baslangic_zamani) UTC olarak
// yazar (datetime.now(UTC)) ama DB sutunu saat dilimsiz oldugundan JSON'da
// UTC ofseti olmadan doner (orn. "2026-08-06T16:54:11"). Buyle bir dizeyi
// duz `new Date(...)`'e vermek tarayiciyi bunu YEREL saat sanmaya iter ve
// buyuk bir kaymaya yol acar — bu yuzden ofset yoksa 'Z' ekleyip UTC oldugunu
// acikca belirtmek gerekir.
export function utcTarihiAyristir(iso: string): Date {
  // Ofset ARANIRKEN yalnızca zaman bölümüne bakılır: tarih bölümündeki tire
  // ("2026-08-08") yanlışlıkla ofset sanılmasın. Kabul edilen biçimler:
  // 'Z'/'z', '+03:00', '+0300', '+03'.
  const zamanBolumu = iso.slice(iso.indexOf('T') + 1)
  const ofsetVar = /(?:[Zz]|[+-]\d{2}:?\d{2}|[+-]\d{2})$/.test(zamanBolumu)
  return new Date(ofsetVar ? iso : `${iso}Z`)
}

// Sürümler ekranı (SDD 6.3.5) oluşturma zamanını "bugün 14:20", "dün 09:04",
// "2 gün önce" biçiminde gösterir — sürümler tipik olarak aynı gün içinde
// arka arkaya üretildiğinden mutlak tarih ayırt edici değil.
export function goreliZaman(iso: string): string {
  const zaman = utcTarihiAyristir(iso)
  const saat = saatBicimle(zaman)

  const bugun = new Date()
  const gunBasi = (t: Date) => new Date(t.getFullYear(), t.getMonth(), t.getDate()).getTime()
  const gunFarki = Math.round((gunBasi(bugun) - gunBasi(zaman)) / 86_400_000)

  const d = etkinDil()
  if (gunFarki <= 0) return `${BUGUN_KUCUK[d]} ${saat}`
  if (gunFarki === 1) return `${GORELI[d].dun} ${saat}`
  return GORELI[d].gunOnce(gunFarki)
}

// "9 Ağustos 2026 14:20" — tarih + saat. Tarih kısmı tarihBicimle'den gelir;
// `toLocaleString` ile ayrı bir sayısal biçim ("09.08 14:20") üretilmez.
export function zamanBicimle(iso: string): string {
  const zaman = utcTarihiAyristir(iso)
  return `${tarihBicimle(isoBicimle(zaman))} ${saatBicimle(zaman)}`
}

function saatBicimle(zaman: Date): string {
  return `${String(zaman.getHours()).padStart(2, '0')}:${String(zaman.getMinutes()).padStart(2, '0')}`
}
