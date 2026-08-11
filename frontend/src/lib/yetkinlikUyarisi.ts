/**
 * Personel formundaki yetkinlik seçiminin ön koşul mantığına etkisi.
 *
 * Ayrı bir dosyada, `kuralAgirlik.ts`teki S1 uyarısıyla aynı gerekçeyle:
 * saf bir karar fonksiyonu bileşenin içinde durursa hem testlenmesi bir
 * ekran kurmayı gerektirir hem de "bu uyarı hangi koşulda çıkıyor"
 * sorusunun yanıtı bir JSX ağacının ortasında aranır.
 */

// SRS 3.3.2'deki karşılıklı dışlayıcı çift. ADLA eşleşir, kimlikle değil:
// kimlikler kuruluma göre değişir, ayrım ise adın kendisinde tanımlı.
const MURACAAT = 'Müracaat Görevlisi'
const GUVENLIK = 'Güvenlik Görevi'

/**
 * Seçilen yetkinlikler ön koşul mantığını bozuyorsa uyarı metni, yoksa null.
 *
 * UYARI, ENGEL DEĞİL. Dışlayıcılık bu modelde ayrı bir kural tipiyle değil
 * YETKİNLİK DAĞILIMIYLA ifade edilir (SRS TD-9); kural hâline getirmek,
 * kataloğa çözücünün hiç görmediği ikinci bir yetkinlik semantiği eklemek
 * ve TD-9'un "yeni bir kural tipi eklemek gerekmez" ilkesini bozmak olurdu.
 * Burada yapılan şey kullanıcıya sonucu söylemek — kararı ona bırakarak.
 */
export function yetkinlikCakismaUyarisi(secilenAdlar: string[]): string | null {
  const kume = new Set(secilenAdlar)
  if (kume.has(MURACAAT) && kume.has(GUVENLIK)) {
    return (
      `${MURACAAT} ile ${GUVENLIK} birlikte seçildi. SRS 3.3.2 bu ikisini karşılıklı ` +
      'dışlayıcı tanımlar: müracaat görevlisi başka bir noktada, güvenlik görevlisi de ' +
      'müracaat noktasında çalışamaz. Kayıt engellenmiyor — bilerek yapıyorsanız devam edin.'
    )
  }
  return null
}
