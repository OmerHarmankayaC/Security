import { Kart, KartEtiketi } from './app-ui'
import { MarkaIsareti } from './Marka'

/**
 * Künye içeriği — İKİ KABUKTA DA AYNI.
 *
 * Yönetici tarafı bunu kendi ekranı olarak (AppShell içinde), çalışan paneli
 * ise üst çubuktaki bağlantıdan açılan bir bölüm olarak gösterir. İçerik iki
 * yerde ayrı yazılsaydı biri güncellendiğinde diğeri geride kalırdı.
 */
export function KunyeIcerigi() {
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
            Vardiya çizelgeleme karar destek aracı
          </p>
        </div>
      </div>
    </Kart>

    <Kart>
      <KartEtiketi>proje</KartEtiketi>
      <p className="m-0 text-sm leading-relaxed text-ink">
        VARDİS, vardiya çizelgesini elle kurmak yerine <strong>kısıt programlama</strong> ile
        üreten bir karar destek aracıdır. Personeli saatlik talebe atarken dinlenme süresi,
        haftalık saat tavanı ve yetkinlik gibi <em>zorunlu</em> kuralları ihlal etmez; gece
        saati, hafta sonu ve toplam yük gibi <em>esnek</em> hedefleri ise adil dağıtmaya
        çalışır.
      </p>
      <p className="m-0 mt-3 text-sm leading-relaxed text-ink">
        Aracın verdiği şey bir emir değil bir öneridir: üretilen her çizelge açıklanabilir —
        hangi kuralın ne kadar cezalandırıldığı, kimin payından ne kadar saptığı ve talebin
        nerede karşılanamadığı ekranda görünür. Karar yöneticidedir; araç yalnızca kararın
        bedelini görünür kılar.
      </p>
    </Kart>

    <Kart>
      <KartEtiketi>geliştirme</KartEtiketi>
      <dl className="m-0 grid grid-cols-[140px_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="text-ink-muted">Rol</dt>
        <dd className="m-0 text-ink">Sistem analisti ve geliştirici — projenin yürütücüsü</dd>
        <dt className="text-ink-muted">Kapsam</dt>
        <dd className="m-0 text-ink">
          Bir yaz stajı çalışması kapsamında geliştirildi; hiçbir kurumun verisini içermez.
        </dd>
      </dl>
      <p className="m-0 mt-3 text-sm leading-relaxed text-ink-muted">
        Uygulamadaki personel, görev noktası ve talep kayıtları <strong>üretilmiş demo
        verisidir</strong>; gerçek bir kadroyu ya da çalışma düzenini yansıtmaz.
      </p>
    </Kart>

    <Kart>
      <KartEtiketi>teknik künye</KartEtiketi>
      <dl className="m-0 grid grid-cols-[140px_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="text-ink-muted">Çözücü</dt>
        <dd className="m-0 text-ink">Google OR-Tools CP-SAT</dd>
        <dt className="text-ink-muted">Sunucu</dt>
        <dd className="m-0 text-ink">Python · FastAPI · SQLAlchemy · Alembic</dd>
        <dt className="text-ink-muted">Arayüz</dt>
        <dd className="m-0 text-ink">React · TypeScript · Vite · Tailwind</dd>
        <dt className="text-ink-muted">Veritabanı</dt>
        <dd className="m-0 text-ink">PostgreSQL</dd>
        <dt className="text-ink-muted">Mimari</dt>
        <dd className="m-0 text-ink">
          Çözücü ayrı bir süreçte koşar; uygulama sunucusu iş kaydı oluşturur, işçi kuyruktan
          alır. İki süreç arasındaki tek sözleşme veritabanıdır.
        </dd>
      </dl>
    </Kart>
    </>
  )
}
