import { type PropsWithChildren, type ReactNode } from 'react'
import type { Rol } from '@/api/types'
import { cn } from '@/lib/utils'
import { buyukHarf } from '@/lib/metin'
import { navGruplari } from '@/lib/yetki'
import { useAktifIs } from './AktifIsBaglami'
import { useOturum } from './OturumBaglami'
import { NAV_SIMGELERI, type NavOgesi } from './nav'
import { Marka } from './Marka'

export type { NavOgesi }

const ROL_ETIKETI: Record<Rol, string> = {
  calisan: 'Çalışan',
  idare: 'İdare',
  hesap_yoneticisi: 'Hesap yöneticisi',
  sistem_yoneticisi: 'Sistem yöneticisi',
}

interface AppShellProps {
  aktifEkran: NavOgesi
  ekranSec: (ekran: NavOgesi) => void
  baslik: string
  altBaslik?: ReactNode
  aksiyonlar?: ReactNode
}

const IS_DURUM_METNI: Record<string, string> = {
  kuyrukta: 'Kuyrukta',
  on_kontrol: 'Ön kontrol',
  cozuluyor: 'Çözülüyor',
  durduruldu: 'Karar bekliyor',
  tamamlandi: 'Tamamlandı',
  uyarili: 'Uyarılı tamamlandı',
  basarisiz: 'Başarısız',
  iptal: 'İptal edildi',
}

function sureBicimle(saniye: number): string {
  const dk = Math.floor(saniye / 60)
  const sn = saniye % 60
  return `${String(dk).padStart(2, '0')}:${String(sn).padStart(2, '0')}`
}

/**
 * Çalışan iş göstergesi (SDD 6.1, SRS FR-4.11).
 *
 * Üst çubukta durur, yani HER EKRANDA görünür: çözüm dakikalar sürebildiği
 * için kullanıcının o süre boyunca Çözüm ekranında beklemesi beklenemez.
 * Karar bekleyen iş de burada görünür — başka ekrandayken durdurup unutan
 * kullanıcının işi sessizce askıda kalmasın.
 *
 * Kaynağı bağlamdır, bağlamın kaynağı da sunucu; bu bileşen hiçbir iş
 * kimliği saklamaz.
 */
function CalisanIsGostergesi({ ekranSec }: { ekranSec: (ekran: NavOgesi) => void }) {
  const { aktifIs, sonuclananIs, bildirimGorunur, gecenSure, sonucuKapat } = useAktifIs()

  const is = aktifIs ?? (bildirimGorunur ? sonuclananIs : null)
  if (is === null) return null
  const kararBekliyor = is.durum === 'durduruldu'
  const bitti = aktifIs === null

  return (
    <button
      type="button"
      onClick={() => {
        if (bitti) sonucuKapat()
        ekranSec('Çözüm')
      }}
      className={cn(
        'flex h-9 items-center gap-3 rounded-sm border px-3 text-sm transition-colors',
        kararBekliyor
          ? 'border-warn/60 bg-warn/10 text-ink hover:bg-warn/20'
          : bitti
            ? 'border-rule bg-surface text-ink-muted hover:bg-sunken'
            : 'border-accent/60 bg-accent/10 text-ink hover:bg-accent/20',
      )}
      title="Çözüm ekranını aç"
    >
      {/* Süren işte nabız; duran işte sabit nokta. Renk tek başına ayrım
          taşımasın diye durum adı da yazılı. */}
      <span
        className={cn(
          'size-2 shrink-0 rounded-full',
          kararBekliyor ? 'bg-warn' : bitti ? 'bg-ink-muted' : 'animate-pulse bg-accent',
        )}
        aria-hidden
      />
      <span className="font-medium">{IS_DURUM_METNI[is.durum] ?? is.durum}</span>
      {!bitti && (
        <span className="font-mono text-mono-kucuk text-ink-muted">{sureBicimle(gecenSure)}</span>
      )}
      {is.en_iyi_ceza !== null && (
        <span className="font-mono text-mono-kucuk text-ink-muted">
          ceza {Number(is.en_iyi_ceza)}
        </span>
      )}
    </button>
  )
}

export function AppShell({
  aktifEkran,
  ekranSec,
  baslik,
  altBaslik,
  aksiyonlar,
  children,
}: PropsWithChildren<AppShellProps>) {
  const { ben, cikis, parolaDegistir } = useOturum()
  return (
    // Kabuk, görünür alanın TAMAMINI kaplar ve kendisi kaydırılmaz
    // (`overflow-hidden`): kaydırma, aşağıdaki içerik alanının kendi
    // işidir. Yan menü böylece sayfayla birlikte inip çıkmaz.
    //
    // `items-start` YAZILMAZ. Yan menü yüksekliğini `h-full` ile kapsayıcının
    // tamamından alıyor; hizalamayı gevşetmek, alt gruptaki Dönem bloğunu
    // (`justify-between` ile aşağı itilen blok) görünür alanın çok altına
    // düşürür — bu bölgede bir kez yaşandı.
    // `h-svh` DEĞİL `flex-1 min-h-0`: üstte gösterim şeridi varken kabuk
    // ayrıca tam bir görüntü yüksekliği isterse toplam şerit kadar taşar ve
    // yan menünün altı (oturum bloğu) ekranın dışında kalır. `min-h-0`
    // olmadan flex öğesi içeriğinden küçülemez ve `overflow-hidden` işe
    // yaramaz.
    <div className="flex min-h-0 flex-1 overflow-hidden bg-canvas text-ink">
      {/* Yan menüde KAYDIRMA YOK (`overflow-hidden`, `overflow-y-auto`
          değil): kaydırma yüzeyi sağdaki içerik alanıdır. Menü kısa ve
          sabit bir listedir; kendi çubuğunu taşıması, sayfanın iki ayrı
          yerinden kaydırılabildiği izlenimi veriyordu. */}
      <aside className="flex h-full w-[260px] shrink-0 flex-col justify-between overflow-hidden bg-chrome-base px-[18px] pt-[26px] pb-[22px]">
        <div className="flex flex-col">
          <Marka />

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
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center justify-between gap-6 border-b border-rule bg-canvas px-7">
          <div className="flex items-center gap-3">
            {/* `başlık/ekran` — Public Sans SemiBold 21px, ayrı bir display
                fontu yok (TASARIM_REFERANSI.md, Tipografi). */}
            <h1 className="m-0 text-baslik-ekran font-semibold text-ink">{baslik}</h1>
            {altBaslik}
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <CalisanIsGostergesi ekranSec={ekranSec} />
            {aksiyonlar && <div className="flex items-center gap-2">{aksiyonlar}</div>}
          </div>
        </header>
        {/* Kaydırılan yüzey burasıdır. Üst çubuk (`shrink-0`) ve yan menü
            yerinde kalır; içindeki `sticky` başlıklar (ör. çizelge
            ızgarası) artık bu alana göre yapışır - üst çubuğun hemen
            altına, sayfanın tepesine değil.

            `[&>*]:shrink-0` ŞART. Kartlar (`ui/card`) `overflow-hidden`
            taşıyor; bir flex öğesinde bu, otomatik asgari boyutu sıfıra
            düşürür. Sabit yükseklikli bir sütunun içinde kartlar o zaman
            TAŞMAK yerine sıkışır ve içeriklerini kırpar — sayılar ve
            butonlar yarım görünür, kaydırma da hiç doğmaz çünkü ortada
            taşan bir şey kalmaz. */}
        <main className="flex flex-1 flex-col gap-5 overflow-y-auto px-8 py-7 [&>*]:shrink-0">
          {children}
        </main>
      </div>
    </div>
  )
}
