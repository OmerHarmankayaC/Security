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
  // `ApiHatasi` sınıf olarak ELDE OLMAYABİLİR: modülü taklit eden bir test
  // onu dışa vurmazsa `instanceof` bir TypeError yükseltir ve o hata TAM DA
  // hata işleyicisinin içinde patlar, yani özgün hatayı gizler. Hata metni
  // üreten bir fonksiyonun yükselmesi, düzeltmeye çalıştığı şeyi imkânsız
  // kılar; bu yüzden sınıfın varlığı önce sınanıyor.
  const apiHatasiMi = typeof ApiHatasi === 'function' && hata instanceof ApiHatasi
  if (apiHatasiMi) {
    const somut = hata as ApiHatasi
    const detay = typeof somut.detay === 'string' ? somut.detay : ''
    const kod = somut.kod
    if (kod !== null && kod in metin.hatalar) {
      return metin.hatalar[kod as HataKodu](detay)
    }
    if (detay !== '') return detay
    // Gövdesi metin OLMAYAN bir yanıt (500, boş 4xx): `ApiHatasi.message`
    // Türkçe bir yedek cümle taşıyor ve onu göstermek İngilizce ekranda
    // Türkçe metin demekti. Durum kodunu sözlükten yazıyoruz.
    return metin.istekBasarisiz(somut.status)
  }
  if (hata instanceof Error && hata.message !== '') return hata.message
  return metin.bilinmeyenHata
}
