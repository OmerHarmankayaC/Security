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
const GUN_KISALTMALARI = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt']
const GUN_TAM_ADLARI = [
  'Pazar',
  'Pazartesi',
  'Salı',
  'Çarşamba',
  'Perşembe',
  'Cuma',
  'Cumartesi',
]
const AY_TAM_ADLARI = [
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
]
const AY_KISALTMALARI = [
  'Oca',
  'Şub',
  'Mar',
  'Nis',
  'May',
  'Haz',
  'Tem',
  'Ağu',
  'Eyl',
  'Eki',
  'Kas',
  'Ara',
]

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
  const tarih = isoAyristir(iso)
  return `${tarih.getDate()} ${AY_TAM_ADLARI[tarih.getMonth()]} ${tarih.getFullYear()}`
}

// "03 – 09 Ağu 2026" (Dönem bloğu, Sayfa İskeleti — Yan menü). Ayrı ay/yıl
// gerektiren nadir durumlarda her iki uca ay adı eklenir. Ayraç en tiredir
// (–), kısa tire değil: iki tarih arasındaki aralığın tipografik karşılığı.
export function donemAraligiBicimle(baslangicIso: string, bitisIso: string): string {
  const b = isoAyristir(baslangicIso)
  const s = isoAyristir(bitisIso)
  const bGun = String(b.getDate()).padStart(2, '0')
  const sGun = String(s.getDate()).padStart(2, '0')
  const sAy = AY_KISALTMALARI[s.getMonth()]
  if (b.getFullYear() === s.getFullYear() && b.getMonth() === s.getMonth()) {
    return `${bGun} – ${sGun} ${sAy} ${s.getFullYear()}`
  }
  const bAy = AY_KISALTMALARI[b.getMonth()]
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
  const tarih = isoAyristir(iso)
  return `${GUN_KISALTMALARI[tarih.getDay()]} ${tarih.getDate()}`.toLocaleUpperCase('tr-TR')
}

// Çalışan Paneli — Vardiyalarım (SDD 6.1): "03 Ağustos Pazartesi".
export function tarihUzunBicim(iso: string): string {
  const tarih = isoAyristir(iso)
  return `${String(tarih.getDate()).padStart(2, '0')} ${AY_TAM_ADLARI[tarih.getMonth()]} ${GUN_TAM_ADLARI[tarih.getDay()]}`
}

// "Bugün" / "Yarın" / tam gün adı ("Çarşamba") — Vardiyalarım listesi ve
// sıradaki vardiya kartı bugunIso'ya göre kıyaslar.
export function gunEtiketi(iso: string, bugunIso: string): string {
  if (iso === bugunIso) return 'Bugün'
  const yarin = new Date(isoAyristir(bugunIso))
  yarin.setDate(yarin.getDate() + 1)
  if (iso === isoBicimle(yarin)) return 'Yarın'
  return GUN_TAM_ADLARI[isoAyristir(iso).getDay()] ?? ''
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

  if (gunFarki <= 0) return `bugün ${saat}`
  if (gunFarki === 1) return `dün ${saat}`
  return `${gunFarki} gün önce`
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
