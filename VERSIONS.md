# Sürüm Sabitleme

SDD 3.4.1 uyarınca, geliştirme ve gösterim ortamları arasındaki sürüm eşliğini
elle korumak için çalışma zamanı sürümleri burada sabitlenir. Bağımlılık
sürümleri için `backend/pyproject.toml` ve `frontend/package.json` esastır.

| Bileşen    | Sürüm     |
|------------|-----------|
| Python     | 3.12+     |
| Node.js    | 22.x      |
| PostgreSQL | 16        |

Not: Bu depodaki geliştirme makinesinde Python 3.13.11 kullanılmıştır;
`backend/pyproject.toml` içindeki `requires-python = ">=3.12"` her iki sürümü
de kapsar. Gösterim sunucusunda 3.12 veya üzeri herhangi bir sürüm kullanılabilir.
