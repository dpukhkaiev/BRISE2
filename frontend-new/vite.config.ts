import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { visualizer } from 'rollup-plugin-visualizer'
import { playwright } from "@vitest/browser-playwright"

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(),
  vuetify({ autoImport: true }),
  visualizer({
    open: true,
    filename: 'dist/stats.html'
  })
  ],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  optimizeDeps: {
    include: ['@stomp/stompjs', '@stomp/rx-stomp']
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('plotly')) {
            return 'plotly-bundle';
          }
        }
      }
    }
  },
  /*
  test: {
    environment: 'jsdom',
    globals: true,
    server: {
      deps: {
        inline: ['vuetify']
      }
    }
  }*/
  test: {
      browser: {
          enabled: true,
          provider: playwright(),
          instances: [
              {
                  browser: "chromium"
              }
          ]
      },
      onConsoleLog(log) {
        console.log(log)
      }
  }
})
