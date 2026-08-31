// Gösterim şeridinin HER YÜZEYDE göründüğü (Demo Senaryosu 10).
//
// Şerit kökte tek yerde çizilir; bu dosya o kararı kilitler. Şerit ekran
// ekran eklenseydi, eklenen bir sonraki ekran onu taşımayı unuturdu ve
// hata sessiz olurdu: eksik bir uyarı, eksik bir düğme gibi görünmez.
//
// İki yüzey ayrı ayrı sınanır çünkü ayrı bileşenler: yönetici arayüzü ve
// çalışan paneli. Üçüncü yüzey giriş ekranı ve o zaten DemoSeridi'nin kendi
// testinde değil, buradaki "oturum yokken" durumunda görünür.
//
// App ve CalisanApp SAHTELENİR: bu testin sorusu şeridin nerede çizildiği,
// o iki ekranın ne çizdiği değil. Gerçekleri bırakılsaydı test, ilgisiz
// onlarca uç noktayı sahtelemek zorunda kalırdı.
import { cleanup, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./App', () => ({ default: () => <div>yönetici arayüzü</div> }))
vi.mock('./CalisanApp', () => ({ CalisanApp: () => <div>çalışan paneli</div> }))

import { Kok } from './Kok'
import { api } from './api/client'
import type { Ben, Rol } from './api/types'
import { ciz } from '@/test/ciz'

function ben(rol: Rol): Ben {
  return {
    kullanici_adi: `demo_${rol}`,
    rol,
    parola_degistirmeli: false,
    personel_id: rol === 'calisan' ? 1 : null,
    ad_soyad: rol === 'calisan' ? 'Fatma Kaya' : null,
  }
}

describe('Kok — gösterim şeridi', () => {
  beforeEach(() => {
    // Otomatik temizlik yok (globals kapalı): önceki testin DOM'u kalırsa
    // "şerit çizilmedi" iddiası, önceki testin şeridini bulup düşer.
    cleanup()
    vi.restoreAllMocks()
    vi.spyOn(api, 'demoKimlik').mockRejectedValue(new Error('404'))
  })

  it('yönetici arayüzünde görünür', async () => {
    vi.spyOn(api, 'ortam').mockResolvedValue({ demo_kipi: true })
    vi.spyOn(api, 'ben').mockResolvedValue(ben('idare'))

    ciz(<Kok />)

    expect(await screen.findByText('yönetici arayüzü')).toBeTruthy()
    expect((await screen.findByRole('status')).textContent).toContain('Gösterim ortamı')
  })

  it('çalışan panelinde görünür', async () => {
    vi.spyOn(api, 'ortam').mockResolvedValue({ demo_kipi: true })
    vi.spyOn(api, 'ben').mockResolvedValue(ben('calisan'))

    ciz(<Kok />)

    expect(await screen.findByText('çalışan paneli')).toBeTruthy()
    expect((await screen.findByRole('status')).textContent).toContain('Gösterim ortamı')
  })

  it('kapalı kipte hiçbir yüzeyde render edilmez', async () => {
    vi.spyOn(api, 'ortam').mockResolvedValue({ demo_kipi: false })
    vi.spyOn(api, 'ben').mockResolvedValue(ben('idare'))

    ciz(<Kok />)

    await screen.findByText('yönetici arayüzü')
    await waitFor(() => expect(api.ortam).toHaveBeenCalled())
    expect(screen.queryByRole('status')).toBeNull()
  })
})
