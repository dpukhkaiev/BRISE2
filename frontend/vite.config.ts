import { fileURLToPath, URL } from 'node:url'
import { configDefaults, defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { visualizer } from 'rollup-plugin-visualizer'
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import { playwright } from '@vitest/browser-playwright'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(),
  vuetify({ autoImport: true }),
  // plotly.js submodules assume Node-like globals (Buffer, global)
  nodePolyfills({
    globals: {
      Buffer: true,
      global: true,
      process: false
    }
  }),
  ...(process.env.ANALYZE ? [visualizer({
    open: true,
    filename: 'dist/stats.html'
  })] : [])
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
  test: {
    globals: true,
    server: {
      deps: {
        inline: ['vuetify']
      }
    },
    projects: [
      {
        extends: true,
        test: {
          name: 'unit',
          environment: 'jsdom',
          exclude: [...configDefaults.exclude, 'src/benchmarks/**']
        }
      },
      {
        // browser-mode runtime benchmarks; run with `npm run bench`
        extends: true,
        test: {
          name: 'benchmark',
          include: ['src/benchmarks/**/*.spec.ts'],
          browser: {
            enabled: true,
            provider: playwright(),
            instances: [
              {
                browser: 'chromium'
              }
            ],
            api: {
              allowWrite: true
            }
          }
        }
      }
    ]
  }
})
