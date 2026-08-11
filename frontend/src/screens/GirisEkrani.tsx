// Giriş ekranı (SRS FR-10.1; SDD 5.1b). Kayıt bağlantısı YOKTUR ve
// olmayacaktır: sistem kurum içi bir araçtır, hesapları yönetim rolü açar
// (SRS 5.10). Ekranda bir "Kayıt ol" bağlantısı, kurumda karşılığı olmayan
// bir yetki vaat ederdi.
//
// Görsel dil Kontrol Odası: koyu şasi zemininde tek bir açık kart. Yönetici
// arayüzünün yan menüsü ve çalışan panelinin üst çubuğu burada yok, çünkü
// henüz hangisine gidileceği belli değil — ekranın taşıdığı tek bağlam
// ürünün kendi adı.
import { useState, type FormEvent } from 'react'
import { api, ApiHatasi } from '@/api/client'
import type { Ben } from '@/api/types'
import { Buton } from '@/components/app-ui'
import { buyukHarf } from '@/lib/metin'

interface Props {
  girisYapildi: (ben: Ben) => void
}

const ALAN_SINIFI =
  'h-9 w-full rounded-sm border border-rule bg-surface px-3 text-sm text-ink outline-none ' +
  'focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

export function GirisEkrani({ girisYapildi }: Props) {
  const [kullaniciAdi, setKullaniciAdi] = useState('')
  const [parola, setParola] = useState('')
  const [hata, setHata] = useState<string | null>(null)
  const [gonderiliyor, setGonderiliyor] = useState(false)

  const gonder = async (olay: FormEvent) => {
    olay.preventDefault()
    setHata(null)
    setGonderiliyor(true)
    try {
      girisYapildi(await api.giris(kullaniciAdi, parola))
    } catch (e) {
      // Sunucunun metni OLDUĞU GİBİ gösterilir; burada zenginleştirilmez.
      // Sunucu, kullanıcının var olup olmadığını ele vermeyecek biçimde tek
      // bir metin döndürüyor (SDD 5.1b); arayüzün "kullanıcı adı yanlış" gibi
      // bir yorum eklemesi o özeni tek satırda geçersiz kılardı.
      setHata(
        e instanceof ApiHatasi
          ? e.message
          : 'Giriş yapılamadı. Bağlantınızı kontrol edin.',
      )
      setGonderiliyor(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-chrome-base px-6">
      <div className="w-full max-w-[380px]">
        <div className="mb-6">
          <p className="m-0 text-base font-semibold tracking-wide text-chrome-ink">
            {buyukHarf('Vardiya Çizelgeleme')}
          </p>
          <p className="m-0 mt-[3px] text-xs text-chrome-ink-muted">karar destek aracı</p>
        </div>

        <form
          onSubmit={gonder}
          className="rounded-md border border-rule bg-surface p-6"
          noValidate
        >
          <p className="mb-4 etiket-caps text-ink-muted">
            {buyukHarf('Giriş')}
          </p>

          <label className="mb-1 block text-sm text-ink-muted" htmlFor="kullanici-adi">
            Kullanıcı adı
          </label>
          <input
            id="kullanici-adi"
            name="kullanici_adi"
            className={ALAN_SINIFI}
            value={kullaniciAdi}
            onChange={(e) => setKullaniciAdi(e.target.value)}
            autoComplete="username"
            autoFocus
          />

          <label className="mt-4 mb-1 block text-sm text-ink-muted" htmlFor="parola">
            Parola
          </label>
          <input
            id="parola"
            name="parola"
            type="password"
            className={ALAN_SINIFI}
            value={parola}
            onChange={(e) => setParola(e.target.value)}
            autoComplete="current-password"
          />

          {hata && (
            <p role="alert" className="mt-4 mb-0 text-sm text-signal">
              {hata}
            </p>
          )}

          <Buton
            varyant="birincil"
            type="submit"
            className="mt-5 w-full"
            disabled={gonderiliyor || !kullaniciAdi || !parola}
          >
            {gonderiliyor ? 'Giriş yapılıyor…' : 'Giriş Yap'}
          </Buton>
        </form>

        <p className="mt-4 text-center text-xs text-chrome-ink-muted">
          Hesabınız yoksa veya parolanızı unuttuysanız yönetime başvurun.
        </p>
      </div>
    </div>
  )
}
