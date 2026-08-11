import { type PropsWithChildren, type ReactNode, useEffect, useState } from 'react'
import { api } from '@/api/client'
import type { Donem, Rol, VardiyaTipi } from '@/api/types'
import { cn } from '@/lib/utils'
import { buyukHarf } from '@/lib/metin'
import { bugunIso, donemAraligiBicimle, gunlerListesi } from '@/lib/tarih'
import { navGruplari } from '@/lib/yetki'
import { useOturum } from './OturumBaglami'
import { NAV_SIMGELERI, type NavOgesi } from './nav'

export type { NavOgesi }

const ROL_ETIKETI: Record<Rol, string> = {
  calisan: 'Çalışan',
  yonetici: 'Yönetici',
  yonetim: 'Yönetim',
}

interface AppShellProps {
  aktifEkran: NavOgesi
  ekranSec: (ekran: NavOgesi) => void
  baslik: string
  altBaslik?: ReactNode
  aksiyonlar?: ReactNode
  // Yan menüdeki "Planlama Dönemi" bloğunun göstereceği dönem. Dönem seçimi
  // olan ekranlar kendi seçimlerini geçirir; geçirmeyen ekranlarda blok
  // aşağıdaki geçerli-dönem kuralına düşer.
  donemId?: number | null
}

/**
 * Yan menüdeki dönem bloğunun hangi dönemi göstereceği.
 *
 * Ekran bir dönem seçmişse o gösterilir. Seçmemişse `/api/donem`'in dönüş
 * SIRASINA GÜVENİLMEZ (sorgu sırasızdır); bunun yerine backend'in çalışan
 * panelinde uyguladığı kuralın aynısı işletilir: bugünü içeren dönem, yoksa
 * en yakın gelecek dönem, o da yoksa en son geçmiş dönem.
 */
function donemSec(donemler: Donem[], donemId: number | null | undefined): Donem | undefined {
  if (donemId != null) {
    const secili = donemler.find((d) => d.donem_id === donemId)
    if (secili) return secili
  }
  const bugun = bugunIso()
  const sirali = [...donemler].sort((a, b) =>
    a.baslangic_tarihi.localeCompare(b.baslangic_tarihi),
  )
  return (
    sirali.find((d) => d.baslangic_tarihi <= bugun && d.bitis_tarihi >= bugun) ??
    sirali.find((d) => d.baslangic_tarihi > bugun) ??
    sirali[sirali.length - 1]
  )
}

export function AppShell({
  aktifEkran,
  ekranSec,
  baslik,
  altBaslik,
  aksiyonlar,
  donemId,
  children,
}: PropsWithChildren<AppShellProps>) {
  const { ben, cikis, parolaDegistir } = useOturum()
  const [donemler, setDonemler] = useState<Donem[]>([])
  const [vardiyaTipleri, setVardiyaTipleri] = useState<VardiyaTipi[]>([])

  useEffect(() => {
    Promise.all([api.donemler(), api.vardiyaTipiListele()])
      .then(([d, v]) => {
        setDonemler(d)
        setVardiyaTipleri(v)
      })
      .catch(() => {
        // Dönem bloğu salt bilgilendirme amaçlı — sessizce boş bırakılır,
        // asıl ekranın kendi veri yükleme hatası zaten görünür olur.
      })
  }, [])

  const donem = donemSec(donemler, donemId)
  const ilkVardiya = vardiyaTipleri[0]
  const vardiyaOzeti = ilkVardiya
    ? `${vardiyaTipleri.length}×${Number(ilkVardiya.sure_saat)}`
    : null

  return (
    <div className="flex min-h-svh bg-canvas text-ink">
      <aside className="sticky top-0 flex h-svh w-[260px] shrink-0 flex-col justify-between overflow-y-auto bg-chrome-base px-[18px] pt-[26px] pb-[22px]">
        <div className="flex flex-col">
          <p className="m-0 text-base font-semibold tracking-wide text-chrome-ink">
            {buyukHarf('Vardiya Çizelgeleme')}
          </p>
          <p className="m-0 mt-[3px] text-xs text-chrome-ink-muted">karar destek aracı</p>

          <nav className="mt-6 flex flex-col">
            {navGruplari(ben.rol).map((grup, i) => (
              <div key={grup.baslik ?? `grup-${i}`} className={cn(i > 0 && 'mt-3.5')}>
                {grup.baslik && (
                  <p className="etiket-caps mb-1 text-chrome-ink-muted">{grup.baslik}</p>
                )}
                <div className="flex flex-col gap-0.5">
                  {grup.ogeler.map((oge) => {
                    const Simge = NAV_SIMGELERI[oge]
                    const aktifMi = oge === aktifEkran
                    return (
                      // Aktif öğenin solundaki 2px accent şerit `border-l` ile
                      // çizilir, ayrı bir konumlandırılmış öğeyle değil; pasif
                      // öğelerde de şeffaf olarak durur, yoksa aktif olan öğe
                      // 2px sağa kayar ve menü seçim değiştikçe titrer.
                      <button
                        key={oge}
                        type="button"
                        className={cn(
                          'flex h-10 items-center gap-[11px] rounded-sm border-l-2 border-transparent px-2.5 text-left text-sm text-chrome-ink-muted transition-colors hover:text-chrome-ink',
                          aktifMi && 'border-accent bg-chrome-raised font-medium text-chrome-ink',
                        )}
                        onClick={() => ekranSec(oge)}
                      >
                        {/* Boyut 17, kontur 2, dolgu yok; rengi `currentColor`
                            olduğu için butonun kendi renginden gelir. */}
                        <Simge size={17} strokeWidth={2} className="shrink-0" aria-hidden />
                        {oge}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </nav>
        </div>

        <div className="flex flex-col gap-[22px]">
          {/* Oturum bloğu, dönem bloğunun üstünde ve aynı "Alt grubu"
              düzeninde: 1px ayraç + etiket/caps başlık. Yan menü bağlam
              taşır ve giriş yapan kişi de bir bağlamdır — ekran eylemleri
              üst çubukta kalır (Tasarım Referansı, arayüz turu notu). */}
          <div className="border-t border-chrome-line pt-3">
            <p className="etiket-caps m-0 text-chrome-ink-muted">{buyukHarf('Oturum')}</p>
            <p className="m-0 mt-1.5 truncate text-sm font-medium text-chrome-ink">
              {ben.ad_soyad ?? ben.kullanici_adi}
            </p>
            {/* Yalnızca kullanıcı adı mono: rol adı ("Yönetici") düz metindir
                ve Mono sayıya/koda ayrılmıştır (TASARIM_REFERANSI.md). */}
            <p className="m-0 mt-0.5 text-mono-kucuk text-chrome-ink-muted">
              <span className="font-mono">{ben.kullanici_adi}</span> · {ROL_ETIKETI[ben.rol]}
            </p>
            <div className="mt-2 flex gap-3">
              <button
                type="button"
                onClick={parolaDegistir}
                className="text-xs text-chrome-ink-muted underline-offset-2 transition-colors hover:text-chrome-ink hover:underline"
              >
                Parola değiştir
              </button>
              <button
                type="button"
                onClick={cikis}
                className="text-xs text-chrome-ink-muted underline-offset-2 transition-colors hover:text-chrome-ink hover:underline"
              >
                Çıkış
              </button>
            </div>
          </div>

          <div className="border-t border-chrome-line pt-3">
            <p className="etiket-caps m-0 text-chrome-ink-muted">
              {buyukHarf('Planlama Dönemi')}
            </p>
            {donem ? (
              <>
                {/* `sayı/orta` — mono, 15px. */}
                <p className="m-0 mt-1.5 font-mono text-sayi-orta font-semibold text-chrome-ink">
                  {buyukHarf(donemAraligiBicimle(donem.baslangic_tarihi, donem.bitis_tarihi))}
                </p>
                {/* `veri/mono-küçük` — dokümanın kendi örneği bu satırı
                    ("7 gün · 3×8 vardiya") mono sayar. */}
                <p className="m-0 mt-0.5 font-mono text-mono-kucuk text-chrome-ink-muted">
                  {gunlerListesi(donem.baslangic_tarihi, donem.bitis_tarihi).length} gün
                  {vardiyaOzeti ? ` · ${vardiyaOzeti} vardiya` : ''}
                </p>
              </>
            ) : (
              <p className="m-0 mt-1.5 text-sm text-chrome-ink-muted">—</p>
            )}
          </div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-6 border-b border-rule bg-canvas px-7">
          <div className="flex items-center gap-3">
            {/* `başlık/ekran` — Public Sans SemiBold 21px, ayrı bir display
                fontu yok (TASARIM_REFERANSI.md, Tipografi). */}
            <h1 className="m-0 text-baslik-ekran font-semibold text-ink">{baslik}</h1>
            {altBaslik}
          </div>
          {aksiyonlar && <div className="flex shrink-0 items-center gap-2">{aksiyonlar}</div>}
        </header>
        <main className="flex flex-col gap-5 px-8 py-7">{children}</main>
      </div>
    </div>
  )
}
