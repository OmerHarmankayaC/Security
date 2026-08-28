# Sürüm Sabitleme

SDD 3.4.1 uyarınca, geliştirme ve gösterim ortamları arasındaki sürüm eşliğini
elle korumak için çalışma zamanı sürümleri burada sabitlenir. Bağımlılık
sürümleri için `backend/pyproject.toml` ve `frontend/package.json` esastır.

| Bileşen    | Sürüm     |
|------------|-----------|
| Python     | 3.12+     |
| Node.js    | 22.x      |
| PostgreSQL | 18        |

PostgreSQL sabiti 16'dan **18**'e çekildi: sabit iki ortamı eşlemek için var
ve 16'da hiçbir ortam koşmuyordu — referans donanım 18.6, geliştirme makinesi
17.x. Geliştirme makinesi 18'e taşınana kadar eşleme tam değildir ve bu
bilinen bir açıktır; şemanın ya da sorguların 16 üstü bir özelliğe bağımlılığı
yoktur, dolayısıyla 16 hâlâ çalışan bir tabandır.

Not: Bu depodaki geliştirme makinesinde Python 3.13.11 kullanılmıştır;
`backend/pyproject.toml` içindeki `requires-python = ">=3.12"` her iki sürümü
de kapsar. Gösterim sunucusunda 3.12 veya üzeri herhangi bir sürüm kullanılabilir.
