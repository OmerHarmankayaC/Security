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
import { useDil } from '@/i18n/DilBaglami'
import { DilSecici } from '@/components/DilSecici'
import { Marka } from '@/components/Marka'
import { DemoKimlikKutusu } from '@/components/DemoKimlikKutusu'

interface Props {
  girisYapildi: (ben: Ben) => void
}

const ALAN_SINIFI =
  'h-9 w-full rounded-sm border border-rule bg-surface px-3 text-sm text-ink outline-none ' +
  'focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

export function GirisEkrani({ girisYapildi }: Props) {
  const { dil, metin: m } = useDil()
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
      setHata(e instanceof ApiHatasi ? e.message : m.giris.baglantiHatasi)
      setGonderiliyor(false)
    }
  }

  // `min-h-svh` DEĞİL `flex-1`: üstte gösterim şeridi varken ekran ayrıca tam
  // bir görüntü yüksekliği isterse toplam taşar ve sayfa kayar — kayınca da
  // gövde rengi ekranın iki ucundan açık bir şerit olarak görünür. Kök bir
  // dikey sütun (index.css) ve burası kalan alanı dolduruyor. `py-8`: içerik
  // gerçekten sığmadığında kayma olur ama kart kenarları ekrana yapışmaz.
  return (
    <div className="flex flex-1 items-center justify-center bg-chrome-base px-6 py-8">
      <div className="w-full max-w-[380px]">
        <div className="mb-6">
          <Marka altBaslik={m.marka.altBaslik} />
        </div>

        <form
          onSubmit={gonder}
          className="rounded-md border border-rule bg-surface p-6"
          noValidate
        >
          <p className="mb-4 etiket-caps text-ink-muted">
            {buyukHarf(m.giris.baslik, dil)}
          </p>

          <label className="mb-1 block text-sm text-ink-muted" htmlFor="kullanici-adi">
            {m.giris.kullaniciAdi}
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
            {m.giris.parola}
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
            {gonderiliyor ? m.giris.gonderiliyor : m.giris.gonder}
          </Buton>
        </form>

        {/* Yalnız gösterim kipinde çizilir; gerçek bir kurulumda uç nokta
            yoktur ve bileşen hiçbir şey render etmez. */}
        <DemoKimlikKutusu
          doldur={(ad, sifre) => {
            setKullaniciAdi(ad)
            setParola(sifre)
            // Hata metni ESKİ denemeye aitti; yeni hesap seçildiğinde
            // ekranda durması, seçilen hesabın reddedildiği izlenimi verirdi.
            setHata(null)
          }}
        />

        <p className="mt-4 text-center text-xs text-chrome-ink-muted">
          {m.giris.yardim}
        </p>

        {/* Dil seçici giriş ekranında da DURMALI: kullanıcı arayüzün dilini
            oturum açmadan önce seçebilmeli, yoksa anlamadığı bir ekranda
            seçiciyi aramak zorunda kalır. */}
        <div className="mt-4 flex justify-center">
          <DilSecici />
        </div>
      </div>
    </div>
  )
}
