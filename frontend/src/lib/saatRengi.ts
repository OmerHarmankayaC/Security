/**
 * Saat renk bandı — TEK YER (SDD 6.3.3, Tur 6 İş 3).
 *
 * RENK ARTIK KATEGORİK DEĞİL. Sabit üç ton (gündüz / akşam / gece) çalışma
 * zamanının bir katalogdan seçildiği sürümlere aitti: renk, bloğun TİPİNİ
 * söylüyordu. Blok kataloğu kalktığı için (SRS TD-13) işaretlenecek bir tip
 * yok; rengin bağlanabileceği tek şey saatin kendisidir ve saat sürekli bir
 * eksendir. Band da bu yüzden süreklidir — 19.59 ile 20.01 arasında bir renk
 * sıçraması, modelde karşılığı olmayan bir sınır çizerdi.
 *
 * RENK TEK BAŞINA BİLGİ TAŞIMAZ. Renk körlüğü ve siyah-beyaz yazdırma
 * nedeniyle şeridin üzerinde saat aralığı metni bulunur (`blok.ts`,
 * `blokErisilebilirEtiket`); bant yalnızca metni destekler. Kilitlilik ve
 * kapsama açığı da renkle DEĞİL dokuyla/şekille gösterilir (`KILIT_DOKUSU`,
 * ızgaranın kapsama satırı) — ikisi de bu bandın içinde bir ton olsaydı
 * bandın kendisi okunamaz hâle gelirdi.
 */

/**
 * Bandın iki ucu — Tasarım Referansı sürüm 4'ün mevcut vardiya renkleri.
 * Yeni bir palet uydurulmadı: kullanıcının tanıdığı en koyu gece ve en açık
 * gündüz tonları uçlarda kalır, aradaki basamaklar onlardan türer.
 */
const GECE_UCU = { r: 0x2f, g: 0x3a, b: 0x38 } // #2F3A38
const GUNDUZ_UCU = { r: 0xe9, g: 0xe7, b: 0xd9 } // #E9E7D9

/**
 * Bandın en koyu olduğu saat.
 *
 * Gece dönemi 20.00–06.00'dır (SRS TD-2) ve ortası 01.00'dir. Bandın dip
 * noktası gece penceresinin ORTASINA konur; pencerenin kenarına konsaydı
 * band pencerenin içinde tek yönlü ilerler ve 20.00 ile 05.00 aynı koyulukta
 * görünmezdi — oysa ikisi de gecenin kenarıdır.
 */
const DIP_SAAT = 1

/** Bandın 0–1 aralığındaki aydınlık değeri; 0 = en koyu gece, 1 = en açık gündüz. */
export function saatAydinligi(saat: number): number {
  return (1 - Math.cos((2 * Math.PI * (saat - DIP_SAAT)) / 24)) / 2
}

function ikilikSayi(deger: number): string {
  return Math.round(deger).toString(16).padStart(2, '0')
}

function karistir(oran: number): string {
  const r = GECE_UCU.r + (GUNDUZ_UCU.r - GECE_UCU.r) * oran
  const g = GECE_UCU.g + (GUNDUZ_UCU.g - GECE_UCU.g) * oran
  const b = GECE_UCU.b + (GUNDUZ_UCU.b - GECE_UCU.b) * oran
  return `#${ikilikSayi(r)}${ikilikSayi(g)}${ikilikSayi(b)}`
}

/**
 * Saat başına renk tablosu, modül yüklenirken bir kez hesaplanır.
 *
 * Otuz personel × yedi gün × yirmi dört dilim beş binden fazla renk sorgusu
 * eder; her birinde kosinüs ve dize birleştirme çalıştırmak ölçülebilir bir
 * maliyettir ve sonuç zaten yalnızca yirmi dört farklı değer alır.
 */
const BAND: readonly string[] = Array.from({ length: 24 }, (_, saat) =>
  karistir(saatAydinligi(saat)),
)

/** Saatin bant rengi. Saat 0–23 dışına düşerse 24'e göre sarılır. */
export function saatRengi(saat: number): string {
  return BAND[((saat % 24) + 24) % 24]!
}

/**
 * O saatin rengi üzerinde okunabilen mürekkep.
 *
 * Eşik aydınlık değerinden değil, bandın gerçek uçlarından çıkarılır: bant
 * doğrusal karıştığından aydınlık 0,5'in altında kaldığı saatler koyu, üstünde
 * kaldığı saatler açık zemindir.
 */
export function saatMurekkebi(saat: number): string {
  return saatAydinligi(((saat % 24) + 24) % 24) < 0.5 ? 'var(--vardiya-gece-ink)' : 'var(--ink)'
}

/**
 * Saat dilimlerinden yatay, SERT DURAKLI bir gradient kurar — mini şeridin ve
 * gün ızgarası bloğunun tek çizim yolu.
 *
 * Tek öğeyle çizmek zorunluluktur, süsleme değil: otuz personel × yedi gün ×
 * yirmi dört dilim beş bin DOM düğümünden fazla eder ve sayfayı boğar
 * (Tur 6 İş 2). Gradient, aynı bilgiyi tek bir arka plan değeriyle taşır.
 *
 * `null` dilim boş saattir ve saydam kalır; boş saati gri boyamak, dolu bir
 * bloğun koyu gece tonuyla karışırdı.
 */
export function saatGradyani(dilimler: readonly (string | null)[]): string {
  if (dilimler.length === 0) return 'none'
  const adim = 100 / dilimler.length
  const duraklar = dilimler.map((renk, i) => {
    const bas = (i * adim).toFixed(4)
    const bit = ((i + 1) * adim).toFixed(4)
    return `${renk ?? 'transparent'} ${bas}% ${bit}%`
  })
  return `linear-gradient(to right, ${duraklar.join(', ')})`
}

/**
 * Bir saat aralığının (yarı açık: `baslangic`–`bitis`) bant gradienti.
 *
 * Saatler bloğun MUTLAK eksenindedir; 22–26 gibi bir aralık gece yarısını
 * aşan bloğun ikinci gününe düşen parçasını doğru renkte boyar.
 */
export function aralikGradyani(baslangic: number, bitis: number): string {
  const uzunluk = Math.max(0, bitis - baslangic)
  return saatGradyani(Array.from({ length: uzunluk }, (_, i) => saatRengi(baslangic + i)))
}

/**
 * Aralığın ortalama aydınlığı — üzerine yazılacak metnin kararı için.
 *
 * Gece yarısını aşan uzun bir blokta bandın bir ucu koyu, öbür ucu açıktır ve
 * tek bir mürekkep rengi ikisinde de okunmaz. Şeridin metni bu yüzden kendi
 * zeminini taşır (`ETIKET_ZEMINI`); ortalama yalnızca kenarlık gibi ikincil
 * kararlar için kullanılır.
 */
export function aralikAydinligi(baslangic: number, bitis: number): number {
  const uzunluk = Math.max(1, bitis - baslangic)
  let toplam = 0
  for (let i = 0; i < uzunluk; i += 1) toplam += saatAydinligi(baslangic + i)
  return toplam / uzunluk
}

/**
 * Şerit üzerindeki saat metninin zemini.
 *
 * Metin doğrudan bandın üzerine yazılamaz: aynı şerit hem #2F3A38 hem #E9E7D9
 * taşıyabildiğinden hiçbir tek mürekkep rengi baştan sona okunmaz. Yarı saydam
 * açık bir zemin bandı gizlemeden metni her iki uçta da okunur kılar.
 */
export const ETIKET_ZEMINI = 'color-mix(in srgb, var(--surface) 84%, transparent)'

/**
 * Kilitli bloğun dokusu — RENK DEĞİL, ÇİZGİ.
 *
 * Kilitlilik bandın içinde bir ton olarak gösterilseydi bandın kendi anlamıyla
 * (saat) karışırdı; eğik tarama bandın üstünde durur ve renkten bağımsız
 * okunur. Aksan renkli dış çizgi ikinci, gereksiz olmayan işarettir: tarama
 * küçük hücrede zayıf kalabilir.
 */
export const KILIT_DOKUSU =
  'repeating-linear-gradient(45deg, color-mix(in srgb, var(--accent) 42%, transparent) 0 2px, transparent 2px 6px)'
