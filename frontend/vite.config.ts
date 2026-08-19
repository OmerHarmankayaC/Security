import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      // Backend adresi ortamdan okunur; varsayılan 8000'dir ve hiçbir
      // kurulumda bunu vermek gerekmez. Aynı makinede 8000'i tutan başka
      // bir uygulama varsa VARDIS_API_PORT ile çakışmadan koşulur.
      '/api': `http://127.0.0.1:${process.env.VARDIS_API_PORT ?? '8000'}`,
    },
  },
})
