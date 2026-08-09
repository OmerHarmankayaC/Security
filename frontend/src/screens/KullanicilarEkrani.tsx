// Kullanıcılar ekranı — yalnız yönetim rolü (SRS FR-10.5).
//
// Düzen Tanımlar ekranıyla bilinçli olarak AYNI: eylemler üst çubuğun
// sağında, aynı sırada; liste aynı `TanimListesi` bileşeni; devre dışı
// bırakma ayrı bir buton değil, düzenleme kipindeki bir alan. Tanımlarda
// "pasifleştirme" için verilen gerekçenin aynısı burada da geçerli —
// kayıt silinmez, geri çekilir (FR-10.5) — ve iki ekranın aynı işi farklı
// biçimde sunması, kullanıcının her ekranda eylemleri yeniden aramasına
// yol açardı.
//
// Ekranın gösterilmesi bir yetki DEĞİLDİR: /api/kullanici sunucuda yönetim
// rolüne kapalıdır ve doğrudan gönderilen istek de reddedilir (FR-10.4).
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { api, ApiHatasi } from '@/api/client'
import type { Kullanici, Personel, Rol } from '@/api/types'
import { AppShell, type NavOgesi } from '@/components/AppShell'
import { TanimListesi, gorunumKur } from '@/components/TanimYonetimi'
import { Buton, Kart, KartEtiketi, Rozet } from '@/components/app-ui'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  /** Kendi hesabında yapılamayacak işlemler için (rol düşürme, kapatma). */
  kendiKullaniciAdi: string
}

const ROLLER: { deger: Rol; etiket: string; aciklama: string }[] = [
  { deger: 'calisan', etiket: 'Çalışan', aciklama: 'Yalnız kendi çizelgesi, özeti ve tercihleri' },
  { deger: 'yonetici', etiket: 'Yönetici', aciklama: 'Vardiya yöneticisinin bütün işlevleri' },
  { deger: 'yonetim', etiket: 'Yönetim', aciklama: 'Yöneticinin yetkileri + hesap yönetimi' },
]

const ROL_ETIKETI: Record<Rol, string> = {
  calisan: 'Çalışan',
  yonetici: 'Yönetici',
  yonetim: 'Yönetim',
}

const ALAN_SINIFI =
  'h-8 w-full rounded-sm border border-rule bg-surface px-2.5 text-sm text-ink outline-none ' +
  'focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30'

export function KullanicilarEkrani({ ekranSec, kendiKullaniciAdi }: Props) {
  const [kullanicilar, setKullanicilar] = useState<Kullanici[]>([])
  const [personeller, setPersoneller] = useState<Personel[]>([])
  const [hata, setHata] = useState<string | null>(null)

  const [seciliId, setSeciliId] = useState<number | null>(null)
  const [kip, setKip] = useState<'kapali' | 'ekle' | 'duzenle' | 'parola'>('kapali')
  const [pasifleriGoster, setPasifleriGoster] = useState(false)

  const yukle = () => {
    Promise.all([api.kullaniciListele(), api.personelListele()])
      .then(([k, p]) => {
        setKullanicilar(k)
        setPersoneller(p)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Hesaplar yüklenemedi'))
  }

  useEffect(yukle, [])

  const secili = useMemo(
    () => kullanicilar.find((k) => k.kullanici_id === seciliId) ?? null,
    [kullanicilar, seciliId],
  )
  const kendisi = secili?.kullanici_adi === kendiKullaniciAdi

  // Hesabı olmayan personel. Bir personelin ikinci hesabı açılamaz (sunucu
  // da reddeder); listeyi baştan süzmek, kullanıcıya seçtirip sonra hata
  // göstermekten iyidir.
  const bagliPersonelIdleri = new Set(
    kullanicilar.map((k) => k.personel_id).filter((x): x is number => x !== null),
  )

  const gorunum = gorunumKur<Kullanici>({
    kayitlar: kullanicilar,
    kimlik: (k) => k.kullanici_id,
    baslik: (k) => k.kullanici_adi,
    ozet: (k) => (
      <>
        {ROL_ETIKETI[k.rol]}
        {k.ad_soyad ? ` · ${k.ad_soyad}` : ''}
        {k.kullanici_adi === kendiKullaniciAdi ? ' · bu hesapla girdiniz' : ''}
      </>
    ),
    aktifMi: (k) => k.aktif,
    ekRozet: (k) => (
      <>
        {k.kilitli_mi && (
          <Rozet varyant="eksik" genislik={72}>
            Kilitli
          </Rozet>
        )}
        {k.parola_degistirmeli && (
          <Rozet varyant="kilitli" genislik={104}>
            Parola bekliyor
          </Rozet>
        )}
      </>
    ),
    bosMesaji: 'Henüz hesap yok.',
  })

  const kapat = () => {
    setKip('kapali')
    yukle()
  }

  return (
    <AppShell
      aktifEkran="Kullanıcılar"
      ekranSec={ekranSec}
      baslik="Kullanıcılar"
      // Tanımlar ekranıyla aynı konum, aynı sıra. "Sil" YOKTUR: hesap
      // silinmez, devre dışı bırakılır ve bu, düzenleme kipindeki bir
      // alandır (FR-10.5).
      aksiyonlar={
        <>
          <Buton
            varyant="birincil"
            onClick={() => {
              setSeciliId(null)
              setKip('ekle')
            }}
          >
            Ekle
          </Buton>
          <Buton
            varyant="ikincil"
            disabled={secili === null}
            title={secili === null ? 'Önce listeden bir hesap seçin' : undefined}
            onClick={() => setKip('duzenle')}
          >
            Değiştir
          </Buton>
          <Buton
            varyant="ikincil"
            disabled={secili === null}
            title={secili === null ? 'Önce listeden bir hesap seçin' : undefined}
            onClick={() => setKip('parola')}
          >
            Parola Sıfırla
          </Buton>
        </>
      }
    >
      {hata && <p className="text-sm text-signal">{hata}</p>}

      <div className="flex items-center justify-end border-b border-rule pb-2">
        <label className="flex shrink-0 items-center gap-2 text-sm text-ink-muted">
          <input
            type="checkbox"
            checked={pasifleriGoster}
            onChange={(e) => setPasifleriGoster(e.target.checked)}
            className="accent-accent"
          />
          Pasifleri göster
        </label>
      </div>

      {(kip === 'ekle' || kip === 'duzenle') && (
        <HesapFormu
          duzenlenen={kip === 'duzenle' ? secili : null}
          kendisi={kendisi}
          personeller={personeller}
          bagliPersonelIdleri={bagliPersonelIdleri}
          onIptal={() => setKip('kapali')}
          onKaydedildi={kapat}
        />
      )}

      {kip === 'parola' && secili && (
        <ParolaSifirlamaFormu
          kullanici={secili}
          onIptal={() => setKip('kapali')}
          onKaydedildi={kapat}
        />
      )}

      <TanimListesi
        gorunum={gorunum}
        seciliId={seciliId}
        seciliIdDegistir={(id) => {
          setSeciliId(id)
          setKip('kapali')
        }}
        pasifleriGoster={pasifleriGoster}
      />
    </AppShell>
  )
}

// --- Ekleme ve değiştirme aynı formdan (Tanımlar ekranındaki desen) --------

interface HesapFormuProps {
  duzenlenen: Kullanici | null
  kendisi: boolean
  personeller: Personel[]
  bagliPersonelIdleri: Set<number>
  onIptal: () => void
  onKaydedildi: () => void
}

function HesapFormu({
  duzenlenen,
  kendisi,
  personeller,
  bagliPersonelIdleri,
  onIptal,
  onKaydedildi,
}: HesapFormuProps) {
  const [kullaniciAdi, setKullaniciAdi] = useState(duzenlenen?.kullanici_adi ?? '')
  const [parola, setParola] = useState('')
  const [rol, setRol] = useState<Rol>(duzenlenen?.rol ?? 'calisan')
  const [personelId, setPersonelId] = useState<number | null>(duzenlenen?.personel_id ?? null)
  const [aktif, setAktif] = useState(duzenlenen?.aktif ?? true)
  const [hata, setHata] = useState<string | null>(null)
  const [kaydediliyor, setKaydediliyor] = useState(false)

  const secilebilirPersoneller = personeller.filter(
    (p) => !bagliPersonelIdleri.has(p.personel_id) || p.personel_id === duzenlenen?.personel_id,
  )

  const gonder = async (olay: FormEvent) => {
    olay.preventDefault()
    setHata(null)
    setKaydediliyor(true)
    try {
      if (duzenlenen) {
        await api.kullaniciGuncelle(duzenlenen.kullanici_id, { rol, aktif, personel_id: personelId })
      } else {
        await api.kullaniciOlustur({
          kullanici_adi: kullaniciAdi,
          parola,
          rol,
          personel_id: personelId,
        })
      }
      onKaydedildi()
    } catch (e) {
      setHata(e instanceof ApiHatasi ? e.message : 'Kaydedilemedi')
      setKaydediliyor(false)
    }
  }

  return (
    <Kart vurgulu>
      <KartEtiketi renk="accent">{duzenlenen ? 'hesabı değiştir' : 'yeni hesap'}</KartEtiketi>
      <form onSubmit={gonder} noValidate>
        <div className="flex flex-wrap gap-4">
          <div className="w-[220px]">
            <label className="mb-1 block text-sm text-ink-muted" htmlFor="hesap-ad">
              Kullanıcı adı
            </label>
            <input
              id="hesap-ad"
              className={ALAN_SINIFI}
              value={kullaniciAdi}
              onChange={(e) => setKullaniciAdi(e.target.value)}
              // Kullanıcı adı sonradan DEĞİŞMEZ: giriş kayıtları ve geçmiş
              // işlemler hesabın kimliğine bağlıdır (FR-10.9).
              disabled={duzenlenen !== null}
              autoComplete="off"
            />
            {duzenlenen === null && (
              <p className="mt-1 mb-0 text-xs text-ink-muted">
                Küçük harf, rakam, nokta, tire; 3–50 karakter.
              </p>
            )}
          </div>

          {duzenlenen === null && (
            <div className="w-[220px]">
              <label className="mb-1 block text-sm text-ink-muted" htmlFor="hesap-parola">
                Başlangıç parolası
              </label>
              <input
                id="hesap-parola"
                type="password"
                className={ALAN_SINIFI}
                value={parola}
                onChange={(e) => setParola(e.target.value)}
                autoComplete="new-password"
              />
              <p className="mt-1 mb-0 text-xs text-ink-muted">
                En az 12 karakter. Kullanıcı ilk girişte değiştirmek zorunda.
              </p>
            </div>
          )}

          <div className="w-[220px]">
            <label className="mb-1 block text-sm text-ink-muted" htmlFor="hesap-rol">
              Rol
            </label>
            <select
              id="hesap-rol"
              className={ALAN_SINIFI}
              value={rol}
              onChange={(e) => setRol(e.target.value as Rol)}
              // Kendi rolünü düşürmek, sistemde hiç yönetim hesabı kalmadığı
              // durumu tek tıkla üretebilir; oradan çıkışın arayüzden yolu
              // yoktur (FR-10.10). Sunucu da reddeder.
              disabled={kendisi}
            >
              {ROLLER.map((r) => (
                <option key={r.deger} value={r.deger}>
                  {r.etiket}
                </option>
              ))}
            </select>
            <p className="mt-1 mb-0 text-xs text-ink-muted">
              {kendisi
                ? 'Kendi rolünüzü değiştiremezsiniz.'
                : ROLLER.find((r) => r.deger === rol)?.aciklama}
            </p>
          </div>

          <div className="w-[260px]">
            <label className="mb-1 block text-sm text-ink-muted" htmlFor="hesap-personel">
              Personel kaydı
            </label>
            <select
              id="hesap-personel"
              className={ALAN_SINIFI}
              value={personelId ?? ''}
              onChange={(e) => setPersonelId(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">— bağlı değil —</option>
              {secilebilirPersoneller.map((p) => (
                <option key={p.personel_id} value={p.personel_id}>
                  {p.ad_soyad} ({p.sicil_no})
                </option>
              ))}
            </select>
            <p className="mt-1 mb-0 text-xs text-ink-muted">
              {rol === 'calisan'
                ? 'Çalışan hesabı bir personel kaydına bağlanmak zorunda.'
                : 'Yönetici ve yönetim rollerinde boş bırakılabilir.'}
            </p>
          </div>

          {duzenlenen !== null && (
            <div className="w-[220px]">
              <p className="mb-1 text-sm text-ink-muted">Durum</p>
              <label className="flex h-8 items-center gap-2 text-sm text-ink">
                <input
                  type="checkbox"
                  checked={aktif}
                  onChange={(e) => setAktif(e.target.checked)}
                  className="accent-accent"
                  disabled={kendisi}
                />
                Aktif
              </label>
              <p className="mt-1 mb-0 text-xs text-ink-muted">
                {kendisi
                  ? 'Kendi hesabınızı kapatamazsınız.'
                  : 'Kapatıldığında hesap silinmez; girişi durur ve açık oturumları kapanır.'}
              </p>
            </div>
          )}
        </div>

        {hata && (
          <p role="alert" className="mt-4 mb-0 text-sm text-signal">
            {hata}
          </p>
        )}

        <div className="mt-5 flex gap-2">
          <Buton varyant="birincil" type="submit" disabled={kaydediliyor}>
            Kaydet
          </Buton>
          <Buton varyant="hayalet" type="button" onClick={onIptal} disabled={kaydediliyor}>
            Vazgeç
          </Buton>
        </div>
      </form>
    </Kart>
  )
}

// --- Parola sıfırlama -------------------------------------------------------

interface ParolaSifirlamaProps {
  kullanici: Kullanici
  onIptal: () => void
  onKaydedildi: () => void
}

function ParolaSifirlamaFormu({ kullanici, onIptal, onKaydedildi }: ParolaSifirlamaProps) {
  const [yeni, setYeni] = useState('')
  const [hata, setHata] = useState<string | null>(null)
  const [kaydediliyor, setKaydediliyor] = useState(false)

  const gonder = async (olay: FormEvent) => {
    olay.preventDefault()
    setHata(null)
    setKaydediliyor(true)
    try {
      await api.kullaniciParolaSifirla(kullanici.kullanici_id, yeni)
      onKaydedildi()
    } catch (e) {
      setHata(e instanceof ApiHatasi ? e.message : 'Sıfırlanamadı')
      setKaydediliyor(false)
    }
  }

  return (
    <Kart vurgulu>
      <KartEtiketi renk="warn">parola sıfırlama</KartEtiketi>
      <form onSubmit={gonder} noValidate>
        <p className="m-0 text-sm text-ink">
          <span className="font-medium">{kullanici.kullanici_adi}</span> hesabına yeni bir
          başlangıç parolası atanacak. Kullanıcı ilk girişte parolayı değiştirmek zorunda
          kalacak ve <span className="font-medium">açık oturumlarının hepsi kapanacak</span>.
        </p>
        <div className="mt-4 w-[260px]">
          <label className="mb-1 block text-sm text-ink-muted" htmlFor="sifirlama-parola">
            Yeni başlangıç parolası
          </label>
          <input
            id="sifirlama-parola"
            type="password"
            className={ALAN_SINIFI}
            value={yeni}
            onChange={(e) => setYeni(e.target.value)}
            autoComplete="new-password"
            autoFocus
          />
          <p className="mt-1 mb-0 text-xs text-ink-muted">En az 12 karakter.</p>
        </div>

        {hata && (
          <p role="alert" className="mt-4 mb-0 text-sm text-signal">
            {hata}
          </p>
        )}

        <div className="mt-5 flex gap-2">
          <Buton varyant="birincil" type="submit" disabled={kaydediliyor || yeni.length === 0}>
            Parolayı Sıfırla
          </Buton>
          <Buton varyant="hayalet" type="button" onClick={onIptal} disabled={kaydediliyor}>
            Vazgeç
          </Buton>
        </div>
      </form>
    </Kart>
  )
}
