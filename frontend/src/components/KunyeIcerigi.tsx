import { Kart, KartEtiketi } from './app-ui'
import { MarkaIsareti } from './Marka'
import { useMetin } from '@/i18n/DilBaglami'

/**
 * Künye içeriği — İKİ KABUKTA DA AYNI.
 *
 * Yönetici tarafı bunu kendi ekranı olarak (AppShell içinde), çalışan paneli
 * ise üst çubuktaki bağlantıdan açılan bir bölüm olarak gösterir. İçerik iki
 * yerde ayrı yazılsaydı biri güncellendiğinde diğeri geride kalırdı.
 */
export function KunyeIcerigi() {
  const m = useMetin()
  return (
    <>
    <Kart>
      <div className="flex items-center gap-3">
        <span className="text-accent">
          <MarkaIsareti boyut={34} />
        </span>
        <div>
          <p className="m-0 text-baslik-ekran font-semibold tracking-tight text-ink">VARDİS</p>
          <p className="m-0 mt-0.5 text-sm text-ink-muted">
            {m.kunye.altBaslik}
          </p>
        </div>
      </div>
    </Kart>

    <Kart>
      <KartEtiketi>{m.kunye.projeBasligi}</KartEtiketi>
      <p className="m-0 text-sm leading-relaxed text-ink">
        {m.kunye.tanitim1}
      </p>
      <p className="m-0 mt-3 text-sm leading-relaxed text-ink">
        {m.kunye.tanitim2}
      </p>
    </Kart>

    <Kart>
      <KartEtiketi>{m.kunye.gelistirmeBasligi}</KartEtiketi>
      <dl className="m-0 grid grid-cols-[140px_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="text-ink-muted">{m.kunye.gelistiren}</dt>
        {/* Kendi adı ATIFTIR, redaksiyon hedefi değil. Bir önceki
            turda kurum adıyla birlikte silinmişti; ikisi aynı şey
            değil — biri ilişki iddiası, diğeri eser sahipliği. */}
        <dd className="m-0 text-ink">Ömer HARMANKAYA</dd>
        <dt className="text-ink-muted">{m.kunye.rolEtiketi}</dt>
        <dd className="m-0 text-ink">{m.kunye.rol}</dd>
        <dt className="text-ink-muted">{m.kunye.kapsam}</dt>
        <dd className="m-0 text-ink">
          {m.kunye.kapsamMetni}
        </dd>
      </dl>
      <p className="m-0 mt-3 text-sm leading-relaxed text-ink-muted">
        {m.kunye.demoNotu}
      </p>
    </Kart>

    <Kart>
      <KartEtiketi>{m.kunye.teknikBaslik}</KartEtiketi>
      <dl className="m-0 grid grid-cols-[140px_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="text-ink-muted">{m.kunye.cozucu}</dt>
        <dd className="m-0 text-ink">Google OR-Tools CP-SAT</dd>
        <dt className="text-ink-muted">{m.kunye.sunucu}</dt>
        <dd className="m-0 text-ink">Python · FastAPI · SQLAlchemy · Alembic</dd>
        <dt className="text-ink-muted">{m.kunye.arayuz}</dt>
        <dd className="m-0 text-ink">React · TypeScript · Vite · Tailwind</dd>
        <dt className="text-ink-muted">{m.kunye.veritabani}</dt>
        <dd className="m-0 text-ink">PostgreSQL</dd>
        <dt className="text-ink-muted">{m.kunye.mimari}</dt>
        <dd className="m-0 text-ink">
          {m.kunye.surecNotu}
        </dd>
      </dl>
    </Kart>
    </>
  )
}
