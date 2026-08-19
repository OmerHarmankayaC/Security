import type { CizelgeSurumu, Donem } from '@/api/types'

/**
 * Hangi dönemin gösterileceği — TEK TANIM.
 *
 * `/api/donem`'in dönüş SIRASINA GÜVENİLMEZ. Uç nokta artan tarihe göre
 * sıralı döner ve listenin ilk öğesini almak EN ESKİ dönemi seçmek demektir;
 * Özet ekranı tam bu hatayı yapıyordu ve kenar çubuğu güncel dönemi yazarken
 * kartlar aylar öncesinin sayılarını gösteriyordu.
 *
 * Kural, backend'in çalışan panelinde uyguladığının aynısıdır: bugünü içeren
 * dönem, yoksa en yakın gelecek dönem, o da yoksa en son geçmiş dönem.
 */
export function donemSec(donemler: readonly Donem[], bugun: string): Donem | undefined {
  const sirali = [...donemler].sort((a, b) =>
    a.baslangic_tarihi.localeCompare(b.baslangic_tarihi),
  )
  return (
    sirali.find((d) => d.baslangic_tarihi <= bugun && d.bitis_tarihi >= bugun) ??
    sirali.find((d) => d.baslangic_tarihi > bugun) ??
    sirali[sirali.length - 1]
  )
}

/**
 * Ölçülebilir en yeni sürüm: ataması olan, yani ÇÖZÜLMÜŞ bir sürüm.
 *
 * Çözülmemiş bir taslağın kapsaması sıfırdır çünkü ataması yoktur — ama bu
 * bir ölçüm değil, bir yokluktur. Özet ekranı taslağın sayılarını ölçüm gibi
 * basınca "kapsama %0 / eksik hücre 0 / toplam ceza —" gibi kendi kendisiyle
 * çelişen bir kart çıkıyordu. Taslak atlanır; hiç ölçülebilir sürüm yoksa
 * çağıran taraf sayı yerine DURUMU söyler.
 */
export function olculebilirSurum(
  surumler: readonly CizelgeSurumu[],
): CizelgeSurumu | undefined {
  return surumler.find((s) => s.durum !== 'taslak')
}
