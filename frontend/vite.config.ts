import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue({
      script: {
        defineModel: true,
        propsDestructure: true
      }
    })
  ],
  server: {
    allowedHosts: true  // 允许所有域名访问（用于 cpolar 等内网穿透）
  },
})
