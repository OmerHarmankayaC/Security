// Gösterim kimlik bilgisi kutusu — YALNIZ giriş ekranında (Demo Senaryosu 7).
//
// Kutu, uç nokta 200 dönerse çizilir. Gerçek bir kurulumda uç nokta yoktur
// (404) ve bu bileşen hiçbir şey render etmez. Karar SUNUCUDA verilir,
// burada değil: ön yüzde bir "demo mu" bayrağına bakıp kutuyu çizmek,
// bayrağın yanlış geldiği bir kurulumda kimlik bilgisini ekrana yazardı.
// Sunucu kaynağı hiç vermiyorsa yazılacak bir şey de yoktur.
//
// Parola PAKETTE DEĞİLDİR. Yanıtla birlikte çalışma zamanında gelir;
// depoda, derlenmiş pakette ve sürüm geçmişinde bulunmaz.
//
// Tek tıkla form doldurmak süs değil: kullanıcı adı ve parolayı elle
// kopyalamak, demoyu gezen kişinin ilk karşılaştığı sürtünme olurdu.
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { DemoHesabi, DemoKimlik, Rol } from '../api/types'

interface Props {
  doldur: (kullaniciAdi: string, parola: string) => void
}

const ROL_BASLIGI: Record<Rol, string> = {
  sistem_yoneticisi: 'Sistem yöneticisi',
  hesap_yoneticisi: 'Hesap yöneticisi',
  idare: 'İdare',
  calisan: 'Çalışan',
}

// Rol sırası ÜRÜNÜN ANLATIM SIRASI: önce çizelgeyi kuran rol, sonra hesap
// yönetimi, en sonda çalışanın kendi paneli. Sunucudan gelen sıraya
// bırakılsaydı liste veritabanı sırasına göre değişirdi.
const ROL_SIRASI: Rol[] = ['idare', 'hesap_yoneticisi', 'calisan']

function rolegoreGrupla(hesaplar: DemoHesabi[]): [Rol, DemoHesabi[]][] {
  return ROL_SIRASI.map((rol) => [rol, hesaplar.filter((h) => h.rol === rol)] as [Rol, DemoHesabi[]])
    .filter(([, liste]) => liste.length > 0)
}

export function DemoKimlikKutusu({ doldur }: Props) {
  const [kimlik, setKimlik] = useState<DemoKimlik | null>(null)

  useEffect(() => {
    // Hata YUTULUR: 404 burada bir arıza değil, olağan durum — gerçek bir
    // kurulumda uç nokta zaten yoktur.
    api
      .demoKimlik()
      .then(setKimlik)
      .catch(() => setKimlik(null))
  }, [])

  if (kimlik === null) return null

  return (
    <section
      aria-label="Gösterim hesapları"
      className="mt-4 rounded-md border border-rule bg-surface p-4"
    >
      <h2 className="m-0 text-xs font-semibold tracking-wide text-ink-muted uppercase">
        Gösterim hesapları
      </h2>
      <p className="m-0 mt-1 text-xs leading-relaxed text-ink-muted">
        Hepsinin parolası aynı: <code className="text-ink">{kimlik.parola}</code>. Bir satıra
        tıklayın, form dolsun.
      </p>

      <ul className="m-0 mt-3 list-none space-y-2 p-0">
        {rolegoreGrupla(kimlik.hesaplar).map(([rol, liste]) => (
          <li key={rol}>
            <span className="text-xs font-semibold text-ink">{ROL_BASLIGI[rol]}</span>
            <ul className="m-0 mt-1 list-none space-y-1 p-0">
              {liste.map((hesap) => (
                <li key={hesap.kullanici_adi}>
                  <button
                    type="button"
                    onClick={() => doldur(hesap.kullanici_adi, kimlik.parola)}
                    className="w-full rounded-sm border border-rule px-2 py-1 text-left text-xs text-ink hover:border-accent focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30 focus-visible:outline-none"
                  >
                    <code className="text-ink">{hesap.kullanici_adi}</code>
                    <span className="ml-2 text-ink-muted">{hesap.aciklama}</span>
                  </button>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  )
}
