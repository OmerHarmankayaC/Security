import type {
  FazlaKadro,
  Atama,
  CizelgeSurumu,
  Donem,
  GorevNoktasi,
  KapsamaAcigi,
  Personel,
} from '@/api/types'
import { geceSaati, saatEtiketi } from './blok'
import { saatiCoz } from './talepAraligi'
import { haftaSonuMu } from './tarih'

/**
 * Çizelge dışa aktarma (FR-8.5, SRS 7.2).
 *
 * Biçimleme ve indirme burada tek yerde durur; Çizelge ve Analiz ekranları
 * aynı fonksiyonları çağırır. Önceki hâlinde CSV üretimi Analiz ekranının
 * içindeydi ve ikinci bir ekrana taşınması kopyalamak anlamına gelirdi.
 */

/**
 * Ayraç noktalı virgül.
 *
 * Türkçe yerelli Excel virgülü ONDALIK ayracı sayar; virgülle ayrılmış bir
 * dosyayı açtığında bütün satırı tek sütuna yığar ve kullanıcı bunu bir veri
 * hatası sanır. Noktalı virgül, Türkçe yerelde liste ayracının kendisidir.
 * RFC 4180 virgülü öngörür, ama bu dosyanın gerçek okuyucusu Excel'dir.
 */
export const CSV_AYRACI = ';'

/**
 * UTF-8 bayt sırası işareti.
 *
 * Excel, kodlama işareti taşımayan bir metin dosyasını Windows'ta sistem kod
 * sayfasıyla (cp1254) açar; "Güvenlik" → "GÃ¼venlik" olur. BOM, dosyayı
 * UTF-8 olarak tanıtan tek taşınabilir işarettir. Diğer araçlar (pandas,
 * awk) BOM'u yok sayar veya `utf-8-sig` ile okur.
 */
export const UTF8_BOM = '﻿'

export interface CizelgeVerisi {
  donem: Donem
  surum: CizelgeSurumu
  atamalar: Atama[]
  kapsamaAcigi: KapsamaAcigi[]
  fazlaKadro: FazlaKadro[]
  personelMap: Map<number, Personel>
  noktaMap: Map<number, GorevNoktasi>
}

/**
 * Uzun biçim başlıkları.
 *
 * SRS 7.2 şu sütunları şart koşar: sicil, ad, tarih, vardiya_tipi, gece_mi,
 * hafta_sonu_mu, sure_saat. Üzerine `gorev_noktasi` eklenir — atama görev
 * noktası kırılımında tutulduğundan (SDD 4.2.4) noktasız bir satır atamanın
 * yarısını taşır.
 *
 * İKİ SÜTUN DEĞİŞTİ (Tur 5). `vardiya_tipi` yerine `baslangic`/`bitis`
 * geldi: blok kataloğu kalktığı için taşınacak bir tip adı yok, bloğun
 * kendisi bir zaman aralığı (SRS TD-13). `gece_mi` ise bayrak olmaktan
 * çıkıp `gece_saat`e döndü — gece HESAPLANIR, işaretlenmez (TD-2) ve
 * ölçünün birimi saattir.
 *
 * BAŞLANGIÇ VE BİTİŞ TAM ISO DAMGASIDIR (Tur 6). Saat metni ("20.00",
 * "06.00") insan içindir ve bu dosyanın okuyucusu makinedir: `tarih` sütunu
 * yanında "20.00; 06.00" gören bir okuyucu, bitişin ertesi güne düştüğünü
 * hiçbir biçimde çıkaramaz — gece yarısını aşan blok tam da bu dosyada
 * görünmez olurdu. Damga sunucudan geldiği gibi yazılır, yeniden
 * türetilmez; saat dilimi ofseti de böylece korunur.
 */
const CIZELGE_BASLIKLARI = [
  'tarih',
  'sicil',
  'ad',
  'baslangic',
  'bitis',
  'gorev_noktasi',
  'gece_saat',
  'hafta_sonu_mu',
  'sure_saat',
] as const

/**
 * Talep sapması başlıkları.
 *
 * SRS 7.2 dört sütun tanımlıyordu: tarih, vardiya_tipi, gorev_noktasi,
 * eksik_sayi. `vardiya_tipi` yerine sapmanın ZAMAN ARALIĞI geliyor (blok
 * kataloğu kalktı, SRS TD-13). Kalan ikisi şu nedenle değişti: dosya artık
 * talepten sapmanın
 * İKİ yönünü birden taşıyor — eksik (kapsama açığı) ve fazla (S1 üst
 * sınırının aşılması). `tur` sütunu ayrımı yapar, `kisi_sayisi` her iki
 * yönde de pozitif kalır ("eksik_sayi = 2, tur = fazla" okunmaz bir
 * satır olurdu).
 *
 * NEDEN AYRI DOSYA DEĞİL. SRS 7.2'nin kapsama açığını çizelgeden ayrı bir
 * dosyaya koyma gerekçesi, iki farklı SATIR ŞEKLİNİN tek dosyada
 * birleşmesiydi ("hiçbir tablo programı böyle bir dosyayı tek tablo
 * olarak açamaz"). Burada şekil aynı: aynı dört anahtar, aynı sayı. Ayrı
 * bir üçüncü dosya, iki ekrana üçüncü bir indirme eklerdi ve "çizelgem
 * talepten nerede saptı" sorusunun yanıtını ikiye bölerdi.
 */
const SAPMA_BASLIKLARI = [
  'tarih',
  'baslangic',
  'bitis',
  'gorev_noktasi',
  'tur',
  'kisi_sayisi',
] as const

/**
 * Tek bir CSV hücresi.
 *
 * Alan ayraç, tırnak veya satır sonu taşıyorsa tırnaklanır; içerideki tırnak
 * ikilenir (RFC 4180). Görev noktası adları kullanıcı tarafından yazıldığı
 * için noktalı virgül içerebilir.
 */
function hucre(deger: string | number): string {
  const metin = String(deger)
  if (metin.includes(CSV_AYRACI) || metin.includes('"') || /[\r\n]/.test(metin)) {
    return `"${metin.replaceAll('"', '""')}"`
  }
  return metin
}

function satir(alanlar: readonly (string | number)[]): string {
  return alanlar.map(hucre).join(CSV_AYRACI)
}

/**
 * CSV gövdesi. Satır sonu CRLF: RFC 4180 bunu öngörür ve Excel'in Windows
 * sürümü LF'li dosyalarda son sütunu bozabiliyor.
 */
function csvBirlestir(satirlar: string[]): string {
  return UTF8_BOM + satirlar.join('\r\n') + '\r\n'
}

/**
 * Uzun biçim: satır başına bir atama.
 *
 * Matris biçimi (personel × gün) tabloya bakmak için iyidir ama veriyle
 * çalışmak için kötüdür — sütun sayısı döneme göre değişir, filtreleme ve
 * gruplama yapılamaz. Matris, yazdırılabilir görünümün işidir.
 *
 * Tarih ISO 8601 kalır (SRS 7.2). Bu, arayüzün her yerinde kullanılan Türkçe
 * biçimden bilinçli bir ayrımdır: dosyanın okuyucusu insan değil bir tablo
 * programıdır, ISO sözlüksel sıralamada takvim sırasıyla aynıdır ve yerel
 * ayardan bağımsız olarak tarih tipine çözülür.
 */
export function cizelgeCsvOlustur(veri: CizelgeVerisi): string {
  const satirlar = veri.atamalar
    .slice()
    .sort((a, b) => a.tarih.localeCompare(b.tarih) || a.personel_id - b.personel_id)
    .map((a) => {
      const personel = veri.personelMap.get(a.personel_id)
      return satir([
        a.tarih,
        personel?.sicil_no ?? '',
        personel?.ad_soyad ?? '',
        a.baslangic_zamani,
        a.bitis_zamani,
        veri.noktaMap.get(a.nokta_id)?.ad ?? '',
        geceSaati(a.baslangic_zamani, a.sure_saat),
        haftaSonuMu(a.tarih) ? 'evet' : 'hayir',
        a.sure_saat,
      ])
    })
  return csvBirlestir([satir(CIZELGE_BASLIKLARI), ...satirlar])
}

/**
 * Kapsama açıkları — ayrı dosya.
 *
 * S1 esnek hedef olduğundan (SRS 4.3) bir çizelgede karşılanmamış talep
 * bulunabilir; yalnızca atamaları veren bir çıktı, o açıkları yok sayarak
 * çizelgeyi olduğundan tam gösterir.
 *
 * Aynı dosyaya ikinci bir bölüm olarak değil AYRI dosyaya yazılır: tek
 * dosyada iki başlık bloğu, uzun biçimin varlık nedenini — makine
 * okunabilirliğini — bozar; hiçbir tablo programı onu tek tablo olarak
 * açamaz. Açık yoksa dosya yalnızca başlık satırını taşır; sıfır satır,
 * "açık yok"un makine okunur karşılığıdır. İnsan okunur karşılığı
 * yazdırılabilir görünümde cümleyle yazılır.
 */
export function kapsamaAcigiCsvOlustur(veri: CizelgeVerisi): string {
  type SapmaSatiri = {
    tarih: string
    baslangic: string
    bitis: string
    nokta_id: number
    tur: 'eksik' | 'fazla'
    kisi_sayisi: number
  }

  const sapmalar: SapmaSatiri[] = [
    ...veri.kapsamaAcigi.map((k) => ({
      tarih: k.tarih,
      baslangic: k.baslangic,
      bitis: k.bitis,
      nokta_id: k.nokta_id,
      tur: 'eksik' as const,
      kisi_sayisi: k.eksik_sayi,
    })),
    ...veri.fazlaKadro.map((f) => ({
      tarih: f.tarih,
      baslangic: f.baslangic,
      bitis: f.bitis,
      nokta_id: f.nokta_id,
      tur: 'fazla' as const,
      kisi_sayisi: f.fazla_sayi,
    })),
  ]

  const satirlar = sapmalar
    .sort(
      (a, b) =>
        a.tarih.localeCompare(b.tarih) ||
        a.baslangic.localeCompare(b.baslangic) ||
        a.nokta_id - b.nokta_id ||
        a.tur.localeCompare(b.tur),
    )
    .map((s) =>
      satir([
        s.tarih,
        saatEtiketi(saatiCoz(s.baslangic)),
        saatEtiketi(saatiCoz(s.bitis, true)),
        veri.noktaMap.get(s.nokta_id)?.ad ?? '',
        s.tur,
        s.kisi_sayisi,
      ]),
    )
  return csvBirlestir([satir(SAPMA_BASLIKLARI), ...satirlar])
}

/**
 * Dosya adı: dönem ve sürüm taşır.
 *
 * Aynı klasöre inen iki çizelge tarayıcıda "cizelge (1).csv" olarak ayrışır;
 * bu ad hangi dönemin hangi sürümü olduğunu söylemez. Tarihler burada da ISO
 * kalır — dosya adları sözlüksel sıralanır ve ISO o sıralamada takvim
 * sırasıyla aynıdır.
 */
export function disaAktarmaDosyaAdi(
  donem: Donem,
  surum: CizelgeSurumu,
  ek: 'cizelge' | 'kapsama-acigi',
  uzanti = 'csv',
): string {
  return `${ek}_${donem.baslangic_tarihi}_${donem.bitis_tarihi}_surum${surum.surum_no}.${uzanti}`
}

/** Metni dosya olarak indirir. Tarayıcı dışında çağrılmaz. */
export function metniIndir(icerik: string, dosyaAdi: string): void {
  const blob = new Blob([icerik], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const baglanti = document.createElement('a')
  baglanti.href = url
  baglanti.download = dosyaAdi
  baglanti.click()
  URL.revokeObjectURL(url)
}

/** Çizelge ve kapsama açığı dosyalarını birlikte indirir. */
export function csvDisaAktar(veri: CizelgeVerisi): void {
  metniIndir(
    cizelgeCsvOlustur(veri),
    disaAktarmaDosyaAdi(veri.donem, veri.surum, 'cizelge'),
  )
  metniIndir(
    kapsamaAcigiCsvOlustur(veri),
    disaAktarmaDosyaAdi(veri.donem, veri.surum, 'kapsama-acigi'),
  )
}
