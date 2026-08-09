import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { Kok } from './Kok.tsx'

// Hangi panelin açılacağı artık ADRESTEN değil OTURUMDAN çıkıyor (SRS 5.10);
// karar `Kok` bileşeninde, sekme başlığı da orada yüzeyle birlikte
// belirleniyor. Önceki hâlde burada `/calisan/{personel_id}?anahtar=...`
// ayrıştırılıyordu; o yol kimlik doğrulamayla birlikte kaldırıldı.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Kok />
  </StrictMode>,
)
