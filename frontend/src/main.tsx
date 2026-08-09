import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { CalisanApp } from './CalisanApp.tsx'

// Çalışan Paneli, kimlik doğrulama YOK (Backlog B-05) — "kişiye özel
// bağlantı" ile girilir: /calisan/{personel_id}?anahtar=... Bir router
// kütüphanesi eklemeden (SDD'de tanımlanmayan bir teknik karar), yönetici
// App'iyle aynı basit "hangi bileşeni render edeceğine burada karar ver"
// deseni kullanılır.
// Sekme başlığı panelle BİRLİKTE seçilir. İkisini ayrı yerlerde belirlemek,
// yeni bir panel eklendiğinde başlığın eski panelde kalması demekti; burada
// tek bir dönüş değeri taşıdıkları için ayrışamazlar.
interface Kok {
  baslik: string
  bilesen: React.ReactElement
}

function kokBileseni(): Kok {
  const parcalar = window.location.pathname.split('/').filter(Boolean)
  if (parcalar[0] === 'calisan') {
    const personelId = Number(parcalar[1])
    const anahtar = new URLSearchParams(window.location.search).get('anahtar') ?? ''
    if (Number.isFinite(personelId) && personelId > 0 && anahtar) {
      return {
        baslik: 'Vardiya — Çalışan',
        bilesen: <CalisanApp personelId={personelId} anahtar={anahtar} />,
      }
    }
    return {
      // Geçersiz bağlantıda panel adı yazılmaz: kişi o panele girememiştir.
      baslik: 'Vardiya',
      bilesen: (
        <div className="flex min-h-svh items-center justify-center bg-canvas px-6 text-center">
          <p className="text-sm text-ink-muted">Bu bağlantı geçersiz.</p>
        </div>
      ),
    }
  }
  return { baslik: 'Vardiya — Admin', bilesen: <App /> }
}

const kok = kokBileseni()
document.title = kok.baslik

createRoot(document.getElementById('root')!).render(<StrictMode>{kok.bilesen}</StrictMode>)
