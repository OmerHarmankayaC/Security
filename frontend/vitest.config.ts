import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

// Test yapılandırması vite.config.ts'ten AYRI tutulur: `test` alanı Vite'ın
// kendi şemasında yok, aynı dosyaya konduğunda `tsc -b` tip hatası veriyor.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      // Bileşen render testleri DOM ister (YazdirilabilirCizelge). Saf
      // yardımcı testleri node ortamında da koşardı; kaynak ağacını tarayan
      // tarih.guard.test.ts dosya başı `@vitest-environment node` ile kendini
      // node'a alır.
      environment: 'jsdom',
    },
  }),
)
