const GUN_KISALTMALARI = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt']
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

// "03 - 09 Ağu 2026" (Dönem bloğu, Sayfa İskeleti — Yan menü). Ayrı ay/yıl
// gerektiren nadir durumlarda her iki uca ay adı eklenir.
export function donemAraligiBicimle(baslangicIso: string, bitisIso: string): string {
  const b = isoAyristir(baslangicIso)
  const s = isoAyristir(bitisIso)
  const bGun = String(b.getDate()).padStart(2, '0')
  const sGun = String(s.getDate()).padStart(2, '0')
  const sAy = AY_KISALTMALARI[s.getMonth()]
  if (b.getFullYear() === s.getFullYear() && b.getMonth() === s.getMonth()) {
    return `${bGun} - ${sGun} ${sAy} ${s.getFullYear()}`
  }
  const bAy = AY_KISALTMALARI[b.getMonth()]
  return `${bGun} ${bAy} - ${sGun} ${sAy} ${s.getFullYear()}`
}

export function gunKisaltmasiVeNumarasi(iso: string): string {
  const tarih = isoAyristir(iso)
  return `${GUN_KISALTMALARI[tarih.getDay()]} ${tarih.getDate()}`.toLocaleUpperCase('tr-TR')
}

// Backend zaman damgalarini (olusturma/guncelleme/baslangic_zamani) UTC olarak
// yazar (datetime.now(UTC)) ama DB sutunu saat dilimsiz oldugundan JSON'da
// UTC ofseti olmadan doner (orn. "2026-08-06T16:54:11"). Buyle bir dizeyi
// duz `new Date(...)`'e vermek tarayiciyi bunu YEREL saat sanmaya iter ve
// buyuk bir kaymaya yol acar — bu yuzden ofset yoksa 'Z' ekleyip UTC oldugunu
// acikca belirtmek gerekir.
export function utcTarihiAyristir(iso: string): Date {
  const ofsetVar = /[zZ]|[+-]\d\d:\d\d$/.test(iso)
  return new Date(ofsetVar ? iso : `${iso}Z`)
}

export function zamanBicimle(iso: string): string {
  return utcTarihiAyristir(iso).toLocaleString('tr-TR', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
  })
}
