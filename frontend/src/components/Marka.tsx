/**
 * VARDİS marka bileşenleri — işaret ve kelime markası.
 *
 * İŞARET ÜRÜNÜN KENDİSİNDEN TÜRETİLDİ. Aracın ekranda yaptığı şey, gün
 * eksenine yerleşmiş çalışma bloklarını göstermektir; işaret de üç bloğu
 * farklı saatlerden başlayan üç şerit olarak taşır. Soyut bir simge yerine
 * ürünün kendi ızgarasının küçültülmüş hâli: kullanıcı ilk kez gördüğünde
 * anlamıyor olsa bile, uygulamayı kullandıktan sonra ne olduğunu anlıyor.
 *
 * Tek dosyada durmasının sebebi, aynı işaretin dört yerde (yönetici kabuğu,
 * giriş ekranı, çalışan paneli, favicon) görünmesi. Dördü ayrı ayrı
 * çizilseydi biri değiştiğinde diğerleri geride kalırdı — bu projede
 * tekrarlayan hata.
 */

/** Şeritlerin (x, genişlik) çiftleri; 24 birimlik gün ekseninde. */
const SERITLER: readonly (readonly [number, number])[] = [
  [1, 9],
  [7, 11],
  [3, 8],
]

export function MarkaIsareti({ boyut = 22 }: { boyut?: number }) {
  return (
    <svg
      width={boyut}
      height={boyut}
      viewBox="0 0 24 24"
      fill="none"
      role="img"
      aria-label="VARDİS"
    >
      <rect width="24" height="24" rx="5" fill="currentColor" opacity="0.14" />
      {SERITLER.map(([x, genislik], i) => (
        <rect
          key={x}
          x={x}
          y={5 + i * 5}
          width={genislik}
          height="3"
          rx="1.5"
          fill="currentColor"
        />
      ))}
    </svg>
  )
}

/**
 * Kelime markası ve altındaki tanım.
 *
 * `koyuZemin` yönetici kabuğu ile çalışan panelinin koyu şasisi içindir;
 * açık zeminde (giriş ekranının kartı) aynı bileşen ters kontrastla durur.
 */
export function Marka({
  koyuZemin = true,
  altBaslik = 'karar destek aracı',
}: {
  koyuZemin?: boolean
  /**
   * Kenar çubuğu 260px'tir ve uzun bir tanım orada iki satıra sarıyor;
   * varsayılan kısa hâldir. Giriş ekranı gibi yeri olan yüzeyler tam
   * tanımı verir.
   */
  altBaslik?: string
}) {
  const baslik = koyuZemin ? 'text-chrome-ink' : 'text-ink'
  const alt = koyuZemin ? 'text-chrome-ink-muted' : 'text-ink-muted'
  return (
    <div className="flex items-center gap-2.5">
      <span className={baslik}>
        <MarkaIsareti />
      </span>
      <span>
        <p className={`m-0 text-baslik-ekran font-semibold tracking-tight ${baslik}`}>VARDİS</p>
        <p className={`m-0 mt-[3px] text-xs ${alt}`}>{altBaslik}</p>
      </span>
    </div>
  )
}
