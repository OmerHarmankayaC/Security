// ETKİN DİL, tek yerde.
//
// Saf yardımcılar (`lib/sayi.ts`, `lib/tarih.ts`) React bağlamını okuyamaz
// ama çıktıları dile bağlıdır: ondalık ayracı, ay adı, gün kısaltması.
// Her birine dil parametresi geçirmek iki yüzden fazla çağrı yerini
// değiştirmek ve biçimleme kuralını o kadar yere dağıtmak demekti.
//
// İKİSİ AYRI AYRI TUTMUYOR. Önce `sayi.ts` kendi yerelini tutuyordu; ikinci
// bir kopya `tarih.ts`e konsaydı aynı olgu iki yerde yaşar ve biri
// güncellenip diğeri unutulduğunda sayılar İngilizce, tarihler Türkçe
// çıkardı. Tek kaynak burasıdır.
//
// TEK YAZAN `DilSaglayici`'dir. Başka hiçbir yerden çağrılmaz; testler
// dışında (onlar da açıkça kurup açıkça geri alırlar).
import { YEREL, type Dil } from './diller'

let _etkin: Dil = 'tr'

export function etkinDiliAyarla(dil: Dil): void {
  _etkin = dil
}

export function etkinDil(): Dil {
  return _etkin
}

/** `Intl` ve `toLocaleUpperCase` için yerel etiketi. */
export function etkinYerel(): string {
  return YEREL[_etkin]
}
