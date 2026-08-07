// Vardiya kodlaması (TASARIM_REFERANSI.md, yalnızca vardiya bağlamındaki
// ızgara/kartlarda kullanılır): gündüz açık/beyaz, akşam sage, gece koyu.
// Vardiya tipinin kendisi bunu taşımadığından (yalnızca gece_mi var)
// başlangıç saatinden yaklaştırılır (bkz. CizelgeEkrani.tsx'teki aynı desen).
export function vardiyaHucreSinifi(geceMi: boolean, baslangicSaati: string): string {
  if (geceMi) return 'bg-vardiya-gece text-vardiya-gece-ink'
  const saat = Number(baslangicSaati.slice(0, 2))
  return saat >= 14 ? 'bg-vardiya-aksam text-ink' : 'bg-vardiya-gunduz text-ink'
}
