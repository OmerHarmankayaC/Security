// Uygulamanın kökü: kim girmiş, hangi yüzey açılacak (SRS 5.10).
//
// Yönlendirme kütüphanesi eklenmedi. Önceki hâlde de eklenmemişti (SDD'de
// tanımlanmayan bir teknik karar olurdu) ve kimlik doğrulama bunu
// gerektirmiyor: yüzey seçimi adresten değil OTURUMDAN çıkıyor. Adres
// çubuğuna bakarak hangi panelin açılacağına karar vermek, kullanıcının
// yazdığı bir yolu yetkiye çevirmek olurdu.
import { useCallback, useEffect, useState } from 'react'
import App from './App'
import { CalisanApp } from './CalisanApp'
import { api, oturumDustugunde } from './api/client'
import type { Ben } from './api/types'
import { DemoSeridi } from './components/DemoSeridi'
import { UcanUyari } from './components/UcanUyari'
import { GirisEkrani } from './screens/GirisEkrani'
import { ParolaDegistirmeEkrani } from './screens/ParolaDegistirmeEkrani'
import { yuzeyBasligi, yuzeySec } from './lib/yetki'
import { useMetin } from './i18n/DilBaglami'

export function Kok() {
  const m = useMetin()
  const [ben, setBen] = useState<Ben | null>(null)
  // Sayfa yenilendiğinde çerez hâlâ geçerli olabilir; giriş ekranını
  // göstermeden önce sunucuya sorulur. Bu bekleme olmasaydı, oturumu açık
  // olan kullanıcı her yenilemede bir an giriş ekranını görürdü.
  const [sorgulandi, setSorgulandi] = useState(false)
  // Kullanıcının kendi isteğiyle açtığı parola değiştirme kipi. Zorunlu
  // kipten (ben.parola_degistirmeli) ayrı tutulur: birinde vazgeçilebilir,
  // diğerinde vazgeçilecek bir yer yoktur.
  const [parolaKipi, setParolaKipi] = useState(false)

  useEffect(() => {
    api
      .ben()
      .then(setBen)
      .catch(() => setBen(null))
      .finally(() => setSorgulandi(true))
  }, [])

  const oturumuBirak = useCallback(() => {
    setBen(null)
    setParolaKipi(false)
  }, [])

  useEffect(() => {
    oturumDustugunde(oturumuBirak)
    return () => oturumDustugunde(null)
  }, [oturumuBirak])

  const yuzey = ben !== null && parolaKipi ? 'parola' : yuzeySec(ben)

  useEffect(() => {
    document.title = yuzeyBasligi(yuzey, m)
  }, [yuzey, m])

  // İlk sorgu bitene kadar hiçbir şey çizilmez. Bir yükleniyor animasyonu
  // koymamak bilinçli: bekleme aynı makinedeki tek bir istek kadar ve
  // görünüp kaybolan bir öğe, ekranı yanıp sönen bir yere çevirir.
  if (!sorgulandi) return null

  // Gösterim şeridi HER yüzeyin üstünde durur, giriş ekranı dahil (Demo
  // Senaryosu 10): veriyi ilk gören kişi henüz giriş yapmamış olabilir.
  // Tek bir yerde çizilir; her ekrana ayrı ayrı eklenseydi bir sonraki
  // ekran onu taşımayı unuturdu.
  const sarmala = (icerik: React.ReactNode) => (
    <>
      <DemoSeridi />
      {icerik}
      {/* Uçan uyarı her yüzeyin üstünde: yazma reddi giriş ekranı dışında
          her ekranda olabilir ve şerit gibi tek yerde çizilir. */}
      <UcanUyari />
    </>
  )

  if (ben === null) return sarmala(<GirisEkrani girisYapildi={setBen} />)

  if (yuzey === 'parola') {
    return sarmala(
      <ParolaDegistirmeEkrani
        ben={ben}
        degistirildi={(yeni) => {
          setBen(yeni)
          setParolaKipi(false)
        }}
        // Zorunlu kipte vazgeçme YOK: diğer uç noktalar sunucuda da kapalı
        // (FR-10.7), vazgeçilse gidilecek bir yer olmazdı.
        vazgec={ben.parola_degistirmeli ? undefined : () => setParolaKipi(false)}
      />,
    )
  }

  const cikis = async () => {
    try {
      await api.cikis()
    } finally {
      // Sunucu hata verse bile arayüz oturumu bırakır: kullanıcının
      // "çıktım" dediği bir ekranda kalması, çıkmadığını fark etmemesi
      // demektir.
      oturumuBirak()
    }
  }

  return sarmala(
    yuzey === 'calisan' ? (
      <CalisanApp ben={ben} cikis={cikis} parolaDegistir={() => setParolaKipi(true)} />
    ) : (
      <App ben={ben} cikis={cikis} parolaDegistir={() => setParolaKipi(true)} />
    ),
  )
}
