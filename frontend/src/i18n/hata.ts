// Sunucu hatasını kullanıcıya gösterilecek metne çevirir.
//
// SIRA ÖNEMLİ ve bilerek böyle: önce kod, sonra sunucunun metni, en sonda
// genel bir cümle.
//
//   1. Kod varsa ve sözlükte tanınıyorsa metin SÖZLÜKTEN yazılır. Doğru
//      olan budur: cümle etkin dilde çıkar.
//   2. Kod yoksa ya da tanınmıyorsa sunucunun `detail`ine düşülür. Bu bir
//      gerileme değil bir GÜVENLİK AĞI: yeni bir kod eklenip sözlüğe
//      yazılmadığında kullanıcı boş bir kutu değil, Türkçe de olsa anlamlı
//      bir cümle görür.
//   3. Hiçbiri yoksa (ağ kopması, 500, gövdesiz yanıt) genel cümle.
//
// Ters sırada kurulsaydı — önce `detail`, sonra kod — çeviri hiç
// çalışmazdı: sunucu her kodlu hataya metin de gönderiyor.
import { ApiHatasi } from '@/api/client'
import type { HataKodu, Metinler } from './sozluk'

export function hataMetni(hata: unknown, metin: Metinler): string {
  if (hata instanceof ApiHatasi) {
    const detay = typeof hata.detay === 'string' ? hata.detay : ''
    const kod = hata.kod
    if (kod !== null && kod in metin.hatalar) {
      return metin.hatalar[kod as HataKodu](detay)
    }
    if (detay !== '') return detay
  }
  if (hata instanceof Error && hata.message !== '') return hata.message
  return metin.bilinmeyenHata
}
