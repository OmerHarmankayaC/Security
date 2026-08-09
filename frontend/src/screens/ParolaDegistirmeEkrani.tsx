// Parola değiştirme (SRS FR-10.7). İki durumda açılır ve ikisi aynı ekrandır:
//
//   zorunlu — yönetimin atadığı/sıfırladığı parolayla ilk giriş. Diğer
//             ekranlar KAPALIDIR; sunucu da öyle davranır, arayüz yalnızca
//             kullanıcıyı boş ekranlarla baş başa bırakmaz.
//   isteğe   — kullanıcı kendi isteğiyle değiştirir; vazgeçip geri dönebilir.
//
// Tek ekran olmasının nedeni, ikisinin gerçekten aynı işlem olması: farklı
// iki ekran, aynı doğrulama kurallarının iki yerde tutulması demekti.
import { useState, type FormEvent } from 'react'
import { api, ApiHatasi } from '@/api/client'
import type { Ben } from '@/api/types'
import { Buton } from '@/components/app-ui'
import { buyukHarf } from '@/lib/metin'

interface Props {
  ben: Ben
  degistirildi: (ben: Ben) => void
  /** Zorunlu kipte verilmez: vazgeçilecek bir yer yoktur. */
  vazgec?: () => void
}

const ALAN_SINIFI =
  'h-9 w-full rounded-sm border border-rule bg-surface px-3 text-sm text-ink outline-none ' +
  'focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

// Sunucudaki kuralın (app/services/parola.py) arayüzdeki karşılığı. İki
// tarafta da bulunması gereksiz değil: arayüz kullanıcıyı istek gitmeden
// durdurup nedenini yazar (NFR-5), sunucu ise sözleşmenin kendisidir ve
// istemciden bağımsız geçerlidir.
const ASGARI_UZUNLUK = 12

export function ParolaDegistirmeEkrani({ ben, degistirildi, vazgec }: Props) {
  const [mevcut, setMevcut] = useState('')
  const [yeni, setYeni] = useState('')
  const [tekrar, setTekrar] = useState('')
  const [hata, setHata] = useState<string | null>(null)
  const [gonderiliyor, setGonderiliyor] = useState(false)

  const zorunlu = ben.parola_degistirmeli
  const kisa = yeni.length > 0 && yeni.length < ASGARI_UZUNLUK
  const uyusmuyor = tekrar.length > 0 && yeni !== tekrar
  const gonderilebilir =
    mevcut.length > 0 && yeni.length >= ASGARI_UZUNLUK && yeni === tekrar && !gonderiliyor

  const gonder = async (olay: FormEvent) => {
    olay.preventDefault()
    setHata(null)
    setGonderiliyor(true)
    try {
      degistirildi(await api.parolaDegistir(mevcut, yeni))
    } catch (e) {
      setHata(e instanceof ApiHatasi ? e.message : 'Parola değiştirilemedi.')
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
          <p className="m-0 mt-[3px] text-xs text-chrome-ink-muted">{ben.kullanici_adi}</p>
        </div>

        <form
          onSubmit={gonder}
          className="rounded-md border border-rule bg-surface p-6"
          noValidate
        >
          <p className="mb-4 font-condensed text-[10px] font-medium tracking-[0.14em] text-ink-muted">
            {buyukHarf('Parola Değiştir')}
          </p>

          {zorunlu && (
            <p className="mt-0 mb-4 text-sm text-ink">
              Parolanız yönetim tarafından atandı. Devam etmeden önce kendi parolanızı
              belirlemelisiniz.
            </p>
          )}

          <label className="mb-1 block text-sm text-ink-muted" htmlFor="mevcut-parola">
            Mevcut parola
          </label>
          <input
            id="mevcut-parola"
            type="password"
            className={ALAN_SINIFI}
            value={mevcut}
            onChange={(e) => setMevcut(e.target.value)}
            autoComplete="current-password"
            autoFocus
          />

          <label className="mt-4 mb-1 block text-sm text-ink-muted" htmlFor="yeni-parola">
            Yeni parola
          </label>
          <input
            id="yeni-parola"
            type="password"
            className={ALAN_SINIFI}
            value={yeni}
            onChange={(e) => setYeni(e.target.value)}
            autoComplete="new-password"
          />
          <p className="mt-1 mb-0 text-xs text-ink-muted">
            En az {ASGARI_UZUNLUK} karakter.
          </p>

          <label className="mt-4 mb-1 block text-sm text-ink-muted" htmlFor="yeni-parola-tekrar">
            Yeni parola (tekrar)
          </label>
          <input
            id="yeni-parola-tekrar"
            type="password"
            className={ALAN_SINIFI}
            value={tekrar}
            onChange={(e) => setTekrar(e.target.value)}
            autoComplete="new-password"
          />

          {kisa && (
            <p className="mt-4 mb-0 text-sm text-signal">
              Yeni parola en az {ASGARI_UZUNLUK} karakter olmalı.
            </p>
          )}
          {uyusmuyor && (
            <p className="mt-4 mb-0 text-sm text-signal">İki parola aynı değil.</p>
          )}
          {hata && (
            <p role="alert" className="mt-4 mb-0 text-sm text-signal">
              {hata}
            </p>
          )}

          <div className="mt-5 flex gap-2">
            <Buton varyant="birincil" type="submit" className="flex-1" disabled={!gonderilebilir}>
              {gonderiliyor ? 'Kaydediliyor…' : 'Parolayı Değiştir'}
            </Buton>
            {vazgec && (
              <Buton varyant="ikincil" type="button" onClick={vazgec} disabled={gonderiliyor}>
                Vazgeç
              </Buton>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
