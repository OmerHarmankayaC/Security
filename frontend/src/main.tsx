import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { Kok } from './Kok.tsx'
import { DilSaglayici } from './i18n/DilBaglami'

// Hangi panelin açılacağı artık ADRESTEN değil OTURUMDAN çıkıyor (SRS 5.10);
// karar `Kok` bileşeninde, sekme başlığı da orada yüzeyle birlikte
// belirleniyor. Önceki hâlde burada `/calisan/{personel_id}?anahtar=...`
// ayrıştırılıyordu; o yol kimlik doğrulamayla birlikte kaldırıldı.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Dil sağlayıcı EN DIŞTA: gösterim şeridi ve giriş ekranı da çevrili
        metin okuyor ve ikisi de oturum açılmadan önce çiziliyor. */}
    <DilSaglayici>
      <Kok />
    </DilSaglayici>
  </StrictMode>,
)
