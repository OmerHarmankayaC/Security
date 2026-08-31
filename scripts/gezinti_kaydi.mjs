// README icin gezinti kaydi: headless Chrome + CDP screencast.
//
// Kareler `Page.captureScreenshot` DONGUSUYLE alinir, `startScreencast`
// ile degil: screencast yalnizca ONDEKI sekmeye akiyor ve headless'ta yeni
// acilan hedef on plana gelmedigi icin hic kare gonderilmedi (denendi, sifir
// kare). Donguyle her kare acikca istenir, gorunurlukten bagimsizdir.
//
// Dongu gezintiyle PARALEL kosar; CDP istekleri kimlikle eslendigi icin
// ikisi ayni baglantiyi paylasabilir. Her karenin alindigi an kaydedilir ve
// ffmpeg'e degisken sureli bir liste (concat demuxer) verilir - sabit kare
// hizi varsayilsaydi is yukune gore uzayan kare araliklari videoyu
// hizlandirip yavaslatirdi.
//
// YAZMA YOK. Kayit boyunca cozum baslatilmaz, kaydedilmez, silinmez; tek
// yazma benzeri eylem giris ve o da oturum acmak icin.

const CDP = 'http://127.0.0.1:9222'
const KOK = 'http://localhost:5180'
const CIKTI = process.argv[2]
const PAROLA = process.env.P
if (!CIKTI || !PAROLA) throw new Error('kullanim: P=<parola> node gezinti.mjs <dizin>')

const { writeFile, mkdir } = await import('node:fs/promises')
await mkdir(`${CIKTI}/kareler`, { recursive: true })

const hedef = await (await fetch(`${CDP}/json/new?about:blank`, { method: 'PUT' })).json()
const ws = new WebSocket(hedef.webSocketDebuggerUrl)
let id = 0
const bekleyen = new Map()
await new Promise((r) => (ws.onopen = r))

let kareNo = 0
const kareler = [] // { ad, zaman }
let kayitAcik = false

ws.onmessage = async (m) => {
  const d = JSON.parse(m.data)
  if (d.id && bekleyen.has(d.id)) {
    const { c, e } = bekleyen.get(d.id)
    bekleyen.delete(d.id)
    d.error ? e(new Error(JSON.stringify(d.error))) : c(d.result)
    return
  }
}

// ZAMAN ASIMI sart: yanitsiz kalan tek bir CDP istegi butun betigi
// susturuyordu. Ilk kayitta gezinti sonuna kadar kostu, sonra bekleyen bir
// `captureScreenshot` hic donmedi ve ffmpeg listesi hic yazilmadi. Reddetmek
// dogru davranis: kare dongusu zaten dusen kareyi yutuyor.
const CDP_ZAMAN_ASIMI_MS = 8000

function cmd(method, params = {}) {
  const i = ++id
  return new Promise((c, e) => {
    const saat = setTimeout(() => {
      bekleyen.delete(i)
      e(new Error(`CDP yanit vermedi: ${method}`))
    }, CDP_ZAMAN_ASIMI_MS)
    const bitir = (f) => (v) => {
      clearTimeout(saat)
      f(v)
    }
    bekleyen.set(i, { c: bitir(c), e: bitir(e) })
    ws.send(JSON.stringify({ id: i, method, params }))
  })
}

const uyu = (ms) => new Promise((r) => setTimeout(r, ms))
const ev = async (x) => {
  const r = await cmd('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails))
  return r.result.value
}

/** Gorunen metne gore tiklar. Sinif adlari tasarimla degisir, etiket degismez. */
async function tikla(metin, { bekle = 2000 } = {}) {
  const ok = await ev(`(() => {
    const b = [...document.querySelectorAll('button, a, [role="tab"]')]
      .find((x) => (x.textContent || '').replace(/\\s+/g, ' ').trim() === ${JSON.stringify(metin)});
    if (!b) return false;
    b.click();
    return true;
  })()`)
  if (!ok) throw new Error(`tiklanacak oge yok: ${metin}`)
  await uyu(bekle)
}

/** Native <select>'i React'in gordugu bicimde ayarlar. */
async function sec(metin, { bekle = 2500 } = {}) {
  const ok = await ev(`(() => {
    for (const s of document.querySelectorAll('select')) {
      const o = [...s.options].find((x) => x.textContent.includes(${JSON.stringify(metin)}));
      if (!o) continue;
      const set = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
      set.call(s, o.value);
      s.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }
    return false;
  })()`)
  if (!ok) throw new Error(`secenek yok: ${metin}`)
  await uyu(bekle)
}

/** Etiketine gore secici; `indis` o secicideki kacinci gercek secenek. */
async function etiketliSec(etiket, indis) {
  const ok = await ev(`(() => {
    const l = [...document.querySelectorAll('label')]
      .find((x) => x.textContent.trim() === ${JSON.stringify(etiket)});
    if (!l) return false;
    const s = l.parentElement.querySelector('select');
    if (!s) return false;
    const secenekler = [...s.options].filter((o) => o.value !== '');
    const o = secenekler[${indis}] ?? secenekler[0];
    if (!o) return false;
    const set = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
    set.call(s, o.value);
    s.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  })()`)
  if (!ok) throw new Error(`secici yok: ${etiket}`)
  await uyu(900)
}

/** Metni iceren ogeyi ekrana getirir. Kor piksel kaydirmasi bolum
    yuksekligi degisince hedefi kaciriyor - kota karti tam boyle kacmisti. */
async function metneKaydir(metin, { bekle = 1800 } = {}) {
  // TURKCE KATLAMA sart: kart etiketleri `buyukHarf()` ile buyutuluyor ve
  // orada "ı" → "I" oluyor. Duz `toLowerCase()` ise "I" → "i" yapar, yani
  // "yıllık" ile "YILLIK" eslesmez. Ilk denemede kota karti tam bu yuzden
  // bulunamadi - `buyukHarf()`in var olma nedeninin ta kendisi.
  const ok = await ev(`(() => {
    const katla = (t) => (t || '')
      .replace(/ı/g, 'i').replace(/İ/g, 'i').replace(/I/g, 'i')
      .toLowerCase().replace(/\s+/g, ' ').trim();
    const aranan = katla(${JSON.stringify(metin)});
    const e = [...document.querySelectorAll('p, h1, h2, h3, span, div')]
      .find((x) => katla(x.textContent) === aranan);
    if (!e) return false;
    e.scrollIntoView({ block: 'center', behavior: 'smooth' });
    return true;
  })()`)
  if (!ok) throw new Error(`kaydirilacak metin yok: ${metin}`)
  await uyu(bekle)
}

/** Yumusak kaydirma: tek sicrayista atlamak videoda okunmuyor. */
async function kaydir(piksel, sure = 1200) {
  await ev(`(() => {
    const k = document.scrollingElement;
    const hedef = document.getElementById('root');
    const alan = hedef && hedef.scrollHeight > hedef.clientHeight ? hedef
      : [...document.querySelectorAll('*')].find((e) => e.scrollHeight > e.clientHeight + 40
          && getComputedStyle(e).overflowY !== 'visible') || k;
    alan.scrollBy({ top: ${piksel}, behavior: 'smooth' });
  })()`)
  await uyu(sure)
}

const KARE_ARALIGI_MS = 110

/** Kayit acikken surekli kare alir; `kayitAcik` false olunca durur. */
async function kareDongusu() {
  while (kayitAcik) {
    const t = Date.now()
    try {
      const { data } = await cmd('Page.captureScreenshot', { format: 'jpeg', quality: 78 })
      const ad = `k${String(kareNo++).padStart(5, '0')}.jpg`
      kareler.push({ ad, zaman: t })
      await writeFile(`${CIKTI}/kareler/${ad}`, Buffer.from(data, 'base64'))
    } catch {
      // Gezinme sirasinda tek tuk kare dusebilir; kayit surer.
    }
    const kalan = KARE_ARALIGI_MS - (Date.now() - t)
    if (kalan > 0) await uyu(kalan)
  }
}

await cmd('Page.enable')
await cmd('Runtime.enable')
// Headless'ta yeni hedef on planda degil; screencast bu yuzden hic kare
// gondermemisti. Dongu bundan bagimsiz calisiyor ama sekmeyi one almak
// yine de dogru: arka plan sekmelerinde zamanlayicilar kisiliyor.
await cmd('Page.bringToFront')
await cmd('Emulation.setDeviceMetricsOverride', {
  width: 1440,
  height: 900,
  deviceScaleFactor: 1,
  mobile: false,
})

// --- Hazirlik (kayit KAPALI) -----------------------------------------------
await cmd('Page.navigate', { url: KOK })
await uyu(2500)
await ev(`fetch('/api/cikis', { method: 'POST', credentials: 'include' })`)
await cmd('Page.navigate', { url: KOK })
await uyu(2500)

// --- Kayit ------------------------------------------------------------------
kayitAcik = true
const basladi = Date.now()
const dongu = kareDongusu()

// 1. Giris ekrani ve kimlik kutusu
await uyu(2500)
await ev(`(() => {
  const b = [...document.querySelectorAll('button')].find((x) => x.textContent.includes('demo_idare'));
  b.scrollIntoView({ block: 'center' });
  b.style.outline = '2px solid rgba(120,180,160,.9)';
})()`)
await uyu(1200)
await tikla('demo_idare  Çizelgeyi kuran ve yayınlayan rol; hesap yönetimi dışındaki her şey', {
  bekle: 1500,
}).catch(async () => {
  // Etiket metni degisebilir; kullanici adiyla ara.
  await ev(`[...document.querySelectorAll('button')].find((x) => x.textContent.includes('demo_idare')).click()`)
  await uyu(1500)
})
await ev(`document.querySelector('button[type=submit]').click()`)
await uyu(3500)

// 2. Ozet
await kaydir(320)
await kaydir(-320)
await uyu(800)

// 3. Cizelge — gun izgarasi, sikisik donem (kapsama seridi + acik rozeti)
await tikla('Çizelge', { bekle: 2500 })
await sec(process.env.SIKISIK)
await uyu(1500)
await kaydir(420)
await uyu(1000)
await kaydir(-420)

// 4. Hafta seridi — yayinlanmis donem
await sec(process.env.GUNCEL)
await tikla('Hafta', { bekle: 2500 })
await kaydir(360)
await uyu(900)
await kaydir(-360)

// 5. Analiz — donem, 90 gun ufku, kota karti
await tikla('Analiz', { bekle: 2500 })
await sec(process.env.GUNCEL)
await uyu(1200)
await tikla('Adalet ufku · 90 gün', { bekle: 2500 })
await uyu(800)
await tikla('Planlama dönemi', { bekle: 2000 })
await kaydir(700)
await uyu(1400)
// KOTA KARTI adiyla hedeflenir; piksel kaydirmasi onu atliyordu.
await metneKaydir('yıllık fazla çalışma kotası', { bekle: 2600 })
await kaydir(-1600)

// 6. Surum karsilastirma
await tikla('Sürümler', { bekle: 2500 })
await sec(process.env.GELECEK)
await uyu(1200)
await tikla('Karşılaştır', { bekle: 1800 })
// Iki surum secici ETIKETIYLE bulunur; sayfadaki donem secicisiyle
// karismasin diye `sec()` degil, etiket metnine gore hedeflenir.
await etiketliSec('Önceki sürüm', 0)
await etiketliSec('Yeni sürüm', 1)
await tikla('Farkları Getir', { bekle: 3000 })
await kaydir(420)
await uyu(1600)

// 7. Calisan paneli
await ev(`fetch('/api/cikis', { method: 'POST', credentials: 'include' })`)
await cmd('Page.navigate', { url: KOK })
await uyu(2500)
await ev(`(() => {
  const b = [...document.querySelectorAll('button')].find((x) => x.textContent.includes('demo_d1010'));
  b.click();
})()`)
await uyu(900)
await ev(`document.querySelector('button[type=submit]').click()`)
await uyu(4000)
await kaydir(400)
await uyu(1000)
await tikla('Dönem Özetim', { bekle: 2800 })
await tikla('Tercihlerim', { bekle: 2800 })
await uyu(1200)

kayitAcik = false
await dongu
const sure = (Date.now() - basladi) / 1000
ws.close()

// --- ffmpeg icin kare listesi ----------------------------------------------
if (kareler.length === 0) throw new Error('hic kare alinamadi')

const satirlar = []
for (let i = 0; i < kareler.length; i++) {
  const bitis = i + 1 < kareler.length ? kareler[i + 1].zaman : kareler[i].zaman + 100
  const sn = Math.max(0.02, (bitis - kareler[i].zaman) / 1000)
  satirlar.push(`file 'kareler/${kareler[i].ad}'`, `duration ${sn.toFixed(3)}`)
}
satirlar.push(`file 'kareler/${kareler.at(-1).ad}'`)
await writeFile(`${CIKTI}/kareler.txt`, satirlar.join('\n') + '\n')

console.log(`kare: ${kareler.length}  süre: ${sure.toFixed(1)} sn`)
process.exit(0)

