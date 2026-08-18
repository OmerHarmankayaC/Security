import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { CozumKarari, Donem, OnKontrolBulgu } from '../api/types'
import { useAktifIs } from '../components/AktifIsBaglami'
import { AppShell, type NavOgesi } from '../components/AppShell'
import { Buton, BuyukRakam, Kart, KartEtiketi, Sayi } from '../components/app-ui'
import { Input } from '@/components/ui/input'
import { cn } from '../lib/utils'
import { buyukHarf } from '../lib/metin'
import { bugunIso, donemAraligiBicimle, gunEkle } from '../lib/tarih'
import {
  AZAMI_DONEM_GUN,
  VARSAYILAN_DONEM_GUN,
  araligiDenetle,
  gunSayisi,
} from '../lib/donemAraligi'

interface Props {
  ekranSec: (ekran: NavOgesi) => void
  donemId: number | null
  donemIdSec: (id: number | null) => void
}

const CALISAN_DURUMLAR = new Set(['kuyrukta', 'on_kontrol', 'cozuluyor'])

const DURUM_METNI: Record<string, string> = {
  kuyrukta: 'Kuyrukta',
  on_kontrol: 'Ön Kontrol',
  cozuluyor: 'Çözülüyor',
  durduruldu: 'Karar Bekleniyor',
  tamamlandi: 'Tamamlandı',
  uyarili: 'Uyarılı Tamamlandı',
  basarisiz: 'Başarısız',
  iptal: 'İptal Edildi',
}

const SECIM_SINIFI =
  'h-8 rounded-sm border border-rule bg-surface px-2.5 font-mono text-sm text-ink outline-none focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/30 disabled:opacity-50'

function sureBicimle(saniye: number): string {
  const dk = Math.floor(saniye / 60)
  const sn = saniye % 60
  return `${String(dk).padStart(2, '0')}:${String(sn).padStart(2, '0')}`
}

/**
 * Hedef bazında ceza dökümü (FR-4.8).
 *
 * Karar paneli ile sonuç özeti aynı dökümü gösterir — panel, çözüm
 * tamamlanmış gibi TAM AYRINTI vermek zorunda (SDD 6.3.2), kullanıcı
 * kararını buna bakarak veriyor. İki kopya bırakmak, birinin sessizce
 * geride kalması demekti.
 */
function CezaDokumu({ girdiler, azami }: { girdiler: [string, number][]; azami: number }) {
  return (
    <ul className="m-0 flex list-none flex-col gap-2 p-0">
      {girdiler.map(([kimlik, deger]) => (
        <li key={kimlik} className="flex items-center gap-3 py-1 text-sm">
          <span className="w-28 shrink-0 text-ink-muted">{kimlik}</span>
          <span className="h-2 flex-1 overflow-hidden rounded-sm bg-sunken">
            <span
              className={kimlik === 'S1' ? 'block h-full bg-signal' : 'block h-full bg-accent'}
              style={{ width: azami > 0 ? `${Math.max(2, (deger / azami) * 100)}%` : '0%' }}
            />
          </span>
          <Sayi className="w-16 shrink-0 text-right text-ink">{deger}</Sayi>
        </li>
      ))}
    </ul>
  )
}

export function CozumEkrani({ ekranSec, donemId, donemIdSec }: Props) {
  const [donemler, setDonemler] = useState<Donem[]>([])
  // Charter 1.6: beş dakika. Çizelge dönemde bir kez üretilir; altmış
  // saniye çözüm kalitesini ürün gerekçesi olmadan sınırlıyordu.
  const [zamanLimiti, setZamanLimiti] = useState(300)

  const [yeniDonemAcik, setYeniDonemAcik] = useState(false)
  const [yeniBaslangic, setYeniBaslangic] = useState('')
  const [yeniBitis, setYeniBitis] = useState('')
  const [donemOlusturuluyor, setDonemOlusturuluyor] = useState(false)

  const [bulgular, setBulgular] = useState<OnKontrolBulgu[] | null>(null)
  const [onKontrolYukleniyor, setOnKontrolYukleniyor] = useState(false)

  const [kapsamaSayisi, setKapsamaSayisi] = useState<number | null>(null)
  const [hata, setHata] = useState<string | null>(null)
  const [kararIsleniyor, setKararIsleniyor] = useState(false)
  const [devamZamanLimiti, setDevamZamanLimiti] = useState(60)

  // İşin kendisi de geçen süre de KABUKTAN gelir; bu ekran ne iş kimliği
  // ne de yoklama döngüsü tutar (SDD 6.1). Ekran değiştirmek bileşeni
  // unmount ediyor ve her ikisi de onunla birlikte ölüyordu.
  const { aktifIs, sonuclananIs, gecenSure, yenile } = useAktifIs()
  const isKaydi = aktifIs ?? sonuclananIs

  useEffect(() => {
    api
      .donemler()
      .then((d) => {
        setDonemler(d)
        if (donemId === null && d[0]) donemIdSec(d[0].donem_id)
      })
      .catch((e) => setHata(e instanceof Error ? e.message : 'Dönemler yüklenemedi'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Sonuçlanan işin kapsama açığı sayısı SÜRÜMDEN okunur, işin kendisinden
  // değil: atamalar yazıldıktan sonra tek doğru kaynak kapsama açığı
  // tablosudur.
  useEffect(() => {
    if (sonuclananIs === null || sonuclananIs.durum === 'iptal') {
      setKapsamaSayisi(null)
      return
    }
    let iptalEdildi = false
    api
      .surumKapsamaAcigi(sonuclananIs.surum_id)
      .then((kapsama) => {
        if (!iptalEdildi) setKapsamaSayisi(kapsama.length)
      })
      .catch(() => {})
    return () => {
      iptalEdildi = true
    }
  }, [sonuclananIs])

  const onKontrolCalistir = async () => {
    if (donemId === null) return
    setOnKontrolYukleniyor(true)
    setHata(null)
    try {
      const yanit = await api.onKontrolCalistir(donemId)
      setBulgular(yanit.bulgular)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Ön kontrol başarısız')
    } finally {
      setOnKontrolYukleniyor(false)
    }
  }

  const cozumBaslat = async () => {
    if (donemId === null) return
    setHata(null)
    setKapsamaSayisi(null)
    try {
      // Dönen iş kaydı KULLANILMAZ; kabuk sunucuya yeniden sorar. Kimliği
      // burada saklamak, aynı bilginin ikinci kopyasını üretirdi.
      await api.cozumBaslat(donemId, zamanLimiti)
      await yenile()
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Çözüm başlatılamadı')
    }
  }

  const durdur = async () => {
    if (!aktifIs) return
    try {
      await api.cozumDurdur(aktifIs.is_id)
      await yenile()
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Durdurma isteği başarısız')
    }
  }

  const kararVer = async (karar: CozumKarari) => {
    if (!aktifIs) return
    if (karar === 'at' && !window.confirm('Bulunan çözüm silinecek. Bu işlem geri alınamaz.')) {
      return
    }
    setKararIsleniyor(true)
    setHata(null)
    try {
      await api.cozumKarari(aktifIs.is_id, karar, devamZamanLimiti)
      // "Devam" yeni bir iş açar, diğer ikisi işi sonlandırır; her iki
      // durumda da yeni gerçeği sunucudan okuruz.
      setKapsamaSayisi(null)
      await yenile()
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Karar uygulanamadı')
    } finally {
      setKararIsleniyor(false)
    }
  }

  const yeniDonemiAc = () => {
    // Varsayılan seçim bir hafta (Backlog 07.08.2026): bugünden başlayan yedi
    // günlük aralık. Kullanıcı iki ucu da takvimden değiştirebilir.
    const bugun = bugunIso()
    setYeniBaslangic(bugun)
    setYeniBitis(gunEkle(bugun, VARSAYILAN_DONEM_GUN - 1))
    setYeniDonemAcik(true)
    setHata(null)
  }

  const yeniDonemOlustur = async () => {
    if (araligiDenetle(yeniBaslangic, yeniBitis)) return
    setDonemOlusturuluyor(true)
    setHata(null)
    try {
      const yeni = await api.donemOlustur({
        baslangic_tarihi: yeniBaslangic,
        bitis_tarihi: yeniBitis,
        // Tercih son bildirim tarihi ayrı bir karar (FR-3.3); dönem
        // oluştururken başlangıç günü varsayılır, Tercihler ekranından
        // değiştirilir.
        tercih_son_tarihi: yeniBaslangic,
      })
      setDonemler((mevcut) => [...mevcut, yeni])
      donemIdSec(yeni.donem_id)
      setYeniDonemAcik(false)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Dönem oluşturulamadı')
    } finally {
      setDonemOlusturuluyor(false)
    }
  }

  const aralikHatasi = yeniDonemAcik ? araligiDenetle(yeniBaslangic, yeniBitis) : null
  const secilenGunSayisi =
    yeniDonemAcik && yeniBaslangic && yeniBitis ? gunSayisi(yeniBaslangic, yeniBitis) : null

  const donem = donemler.find((d) => d.donem_id === donemId) ?? null
  const calisiyorMu = isKaydi !== null && CALISAN_DURUMLAR.has(isKaydi.durum)
  const kararBekliyorMu = isKaydi !== null && isKaydi.durum === 'durduruldu'
  const sonuclandiMi = isKaydi !== null && !calisiyorMu && !kararBekliyorMu
  // Devam eden iş varken "Çözümü Başlat" pasiftir (SDD 6.3.2) — KARAR
  // BEKLEYEN iş de buna dahil. Değilse, yeni bir çözüm başlatmak karar
  // bekleyen işi göstergeden düşürür ve kullanıcı bir daha ona dönemez:
  // iş, kararı verilmeden askıda kalır.
  const yeniCozumEngelli = calisiyorMu || kararBekliyorMu

  const cezaGirdileri = isKaydi?.ceza_dokumu
    ? Object.entries(isKaydi.ceza_dokumu).sort(([a], [b]) => a.localeCompare(b))
    : []
  const azamiCeza = cezaGirdileri.reduce((azami, [, deger]) => Math.max(azami, deger), 0)

  return (
    <AppShell aktifEkran="Çözüm" ekranSec={ekranSec} baslik="Çözüm" donemId={donemId}>
      <Kart>
        <KartEtiketi>çözüm ayarları</KartEtiketi>
        <div className="flex flex-wrap items-end gap-6">
          <div className="flex flex-col gap-1">
            <label htmlFor="donem-sec" className="text-sm text-ink-muted">
              Dönem
            </label>
            <select
              id="donem-sec"
              className={SECIM_SINIFI}
              value={donemId ?? ''}
              onChange={(e) => donemIdSec(e.target.value ? Number(e.target.value) : null)}
            >
              {donemler.map((d) => (
                <option key={d.donem_id} value={d.donem_id}>
                  {donemAraligiBicimle(d.baslangic_tarihi, d.bitis_tarihi)}
                </option>
              ))}
            </select>
          </div>
          <Buton varyant="ikincil" onClick={yeniDonemiAc} disabled={yeniDonemAcik}>
            Yeni Dönem
          </Buton>
          <div className="flex flex-col gap-1">
            <label htmlFor="zaman-limiti" className="text-sm text-ink-muted">
              Zaman Limiti (saniye)
            </label>
            <Input
              id="zaman-limiti"
              type="number"
              min={1}
              className="w-32 rounded-sm border-rule font-mono"
              value={zamanLimiti}
              onChange={(e) => setZamanLimiti(Number(e.target.value))}
            />
          </div>
          <div className="flex gap-2">
            <Buton
              varyant="ikincil"
              onClick={onKontrolCalistir}
              disabled={donemId === null || onKontrolYukleniyor}
            >
              Ön Kontrol
            </Buton>
            <Buton
              varyant="birincil"
              onClick={cozumBaslat}
              disabled={donemId === null || yeniCozumEngelli}
            >
              Çözümü Başlat
            </Buton>
          </div>
        </div>

        {yeniDonemAcik && (
          <div className="mt-5 border-t border-rule pt-4">
            <KartEtiketi>yeni planlama dönemi</KartEtiketi>
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="donem-baslangic" className="text-sm text-ink-muted">
                  Başlangıç
                </label>
                <Input
                  id="donem-baslangic"
                  type="date"
                  className="w-44 rounded-sm border-rule font-mono"
                  value={yeniBaslangic}
                  onChange={(e) => setYeniBaslangic(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label htmlFor="donem-bitis" className="text-sm text-ink-muted">
                  Bitiş
                </label>
                <Input
                  id="donem-bitis"
                  type="date"
                  className="w-44 rounded-sm border-rule font-mono"
                  value={yeniBitis}
                  // Takvim, kabul edilemez tarihleri en baştan göstermesin;
                  // aralık denetimi yine de kalır (kullanıcı elle yazabilir).
                  min={yeniBaslangic || undefined}
                  max={
                    yeniBaslangic ? gunEkle(yeniBaslangic, AZAMI_DONEM_GUN - 1) : undefined
                  }
                  onChange={(e) => setYeniBitis(e.target.value)}
                />
              </div>
              <Buton
                varyant="birincil"
                onClick={yeniDonemOlustur}
                disabled={donemOlusturuluyor || aralikHatasi !== null}
              >
                Dönemi Oluştur
              </Buton>
              <Buton varyant="hayalet" onClick={() => setYeniDonemAcik(false)}>
                İptal
              </Buton>
            </div>
            {aralikHatasi ? (
              <p className="mt-2 text-sm text-signal">{aralikHatasi}</p>
            ) : (
              <p className="mt-2 text-sm text-ink-muted">
                Seçilen aralık <Sayi>{secilenGunSayisi}</Sayi> gün · en fazla{' '}
                <Sayi>{AZAMI_DONEM_GUN}</Sayi> gün
              </p>
            )}
          </div>
        )}

        {bulgular && (
          <div className="mt-4">
            {bulgular.length === 0 ? (
              <p className="text-sm text-ink-muted">Yapısal bir engel bulunamadı.</p>
            ) : (
              // Engel ile uyarı ayrı gösterilir ve ayrı sayılır: engel varken
              // çözüm zaten başlamaz, uyarı varken başlar. İkisini aynı kırmızı
              // listede toplamak, kullanıcının çözümün duracağını sanmasına
              // (ya da tersine, uyarıyı engel sanıp yok saymasına) yol açar.
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {bulgular.map((b, i) => (
                  <li
                    key={i}
                    className={cn(
                      'border-l-2 pl-3 text-sm',
                      b.kesin_mi
                        ? 'border-signal text-signal'
                        : 'border-accent text-ink',
                    )}
                  >
                    <span className="etiket-caps text-ink-muted">
                      {buyukHarf(b.kesin_mi ? 'Engel' : 'Uyarı')}
                    </span>
                    <br />
                    {b.aciklama}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </Kart>

      {hata && <p className="text-sm text-signal">{hata}</p>}

      {isKaydi && calisiyorMu && (
        <Kart vurgulu>
          <KartEtiketi renk="accent">{DURUM_METNI[isKaydi.durum] ?? isKaydi.durum}</KartEtiketi>
          <div className="mb-4 flex gap-10">
            <BuyukRakam deger={sureBicimle(gecenSure)} etiket="Geçen Süre" />
            <BuyukRakam
              deger={isKaydi.en_iyi_ceza !== null ? isKaydi.en_iyi_ceza : '—'}
              etiket="En İyi Ceza"
            />
            <BuyukRakam deger="—" etiket="Kapsama Açığı" />
          </div>
          <Buton varyant="hayalet" onClick={durdur}>
            Durdur
          </Buton>
          {/* SDD 5.4.1: karar noktası yalnızca arama sürerken doğar.
              Kuyruktaki ya da ön kontroldeki bir işte saklanacak bir sonuç
              olmadığı için durdurma doğrudan iptaldir; metin hangi durumda
              ne olacağını önceden söyler. */}
          <p className="mt-2 text-sm text-ink-muted">
            {isKaydi.durum === 'cozuluyor'
              ? 'Durdur, aramayı sonlandırır; o ana kadar bulunmuş çözüm atılmaz, kararınız için saklanır.'
              : 'Arama henüz başlamadı. Durdur, işi doğrudan iptal eder; saklanacak bir sonuç olmadığı için karar sorulmaz.'}
          </p>
        </Kart>
      )}

      {isKaydi && kararBekliyorMu && (
        <Kart vurgulu>
          <KartEtiketi renk="warn">karar bekleniyor</KartEtiketi>
          <p className="mb-4 text-sm text-ink-muted">
            Arama sonlandırıldı. Bulunan çözüm henüz çizelgeye yazılmadı; sürüm durdurma
            öncesindeki hâlinde duruyor.
          </p>
          <div className="mb-4 flex gap-10">
            <BuyukRakam deger={sureBicimle(gecenSure)} etiket="Geçen Süre" />
            <BuyukRakam
              deger={isKaydi.en_iyi_ceza !== null ? isKaydi.en_iyi_ceza : '—'}
              etiket="Toplam Ceza"
            />
            <BuyukRakam
              deger={isKaydi.gecici_kapsama_acigi_sayisi?.toString() ?? '—'}
              etiket="Kapsama Açığı"
            />
          </div>

          {cezaGirdileri.length > 0 && <CezaDokumu girdiler={cezaGirdileri} azami={azamiCeza} />}

          {!isKaydi.kullanilabilir_sonuc_var && (
            <p className="mt-4 text-sm text-signal">
              {isKaydi.hata_mesaji ??
                'Çözücü ilk uygun çizelgeye ulaşmadan durduruldu; kullanılabilir bir sonuç yok.'}{' '}
              Bu nedenle "Sonucu kullan" seçilemiyor.
            </p>
          )}

          <div className="mt-5 flex flex-wrap items-end gap-3">
            <Buton
              varyant="birincil"
              onClick={() => kararVer('kullan')}
              disabled={kararIsleniyor || !isKaydi.kullanilabilir_sonuc_var}
            >
              Sonucu kullan
            </Buton>
            <Buton
              varyant="hayalet"
              onClick={() => kararVer('at')}
              disabled={kararIsleniyor}
            >
              Sonucu at
            </Buton>
            <div className="flex flex-col gap-1">
              <label htmlFor="devam-zaman-limiti" className="text-sm text-ink-muted">
                Yeni zaman limiti (saniye)
              </label>
              <Input
                id="devam-zaman-limiti"
                type="number"
                min={1}
                className="w-32 rounded-sm border-rule font-mono"
                value={devamZamanLimiti}
                onChange={(e) => setDevamZamanLimiti(Number(e.target.value))}
              />
            </div>
            <Buton
              varyant="ikincil"
              onClick={() => kararVer('devam')}
              disabled={kararIsleniyor || devamZamanLimiti < 1}
            >
              Bu çözümden devam et
            </Buton>
          </div>
          {/* SDD 5.4.1: "kaldığı yerden devam" DEĞİLDİR. Çözücü
              sonlandırıldıktan sonra iç arama durumu geri yüklenemez;
              bulunan çözüm ipucu verilerek YENİ bir arama başlar. Ekranın
              bunu yazması, kullanıcının sürenin kaldığı yerden işlediğini
              sanmasını engeller. */}
          <p className="mt-3 text-sm text-ink-muted">
            "Devam et", bulunan çözümü başlangıç ipucu olarak veren{' '}
            <strong className="font-medium text-ink">yeni bir arama</strong> başlatır; süre
            sıfırdan işler ve sonuç bu çözümden kötü olmaz.
          </p>
        </Kart>
      )}

      {isKaydi && sonuclandiMi && (
        <Kart>
          <KartEtiketi renk={isKaydi.durum === 'tamamlandi' ? undefined : 'warn'}>
            sonuç özeti — {DURUM_METNI[isKaydi.durum] ?? isKaydi.durum}
          </KartEtiketi>
          {isKaydi.hata_mesaji && <p className="text-sm text-signal">{isKaydi.hata_mesaji}</p>}
          {/* İptal edilen işte karar paneli HİÇ açılmaz (SDD 5.4.1); işin ne
              olduğu burada yazılı kalır, yoksa kullanıcı beklediği paneli
              arar. */}
          {isKaydi.durum === 'iptal' && (
            <p className="text-sm text-ink-muted">
              İş iptal edildi. Çizelge sürümü değişmedi.
            </p>
          )}
          {cezaGirdileri.length > 0 && <CezaDokumu girdiler={cezaGirdileri} azami={azamiCeza} />}
          {kapsamaSayisi !== null && kapsamaSayisi > 0 && (
            <p className="mt-2 text-sm text-ink-muted">
              {kapsamaSayisi} kapsama açığı bulundu → Çizelge ekranında ilgili hücreler
              işaretlendi.
            </p>
          )}
          {donem && (
            <Buton varyant="hayalet" className="mt-4" onClick={() => ekranSec('Çizelge')}>
              Çizelgeyi Görüntüle
            </Buton>
          )}
        </Kart>
      )}
    </AppShell>
  )
}
