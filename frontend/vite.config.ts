import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// Builds into ../static/app, which Flask serves at /static/app/; frontend_assets.py reads the manifest
// to put the entry script on the pages.
export default defineConfig({
  plugins: [react()],
  base: '/static/app/',
  build: {
    outDir: '../static/app',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: { input: 'src/main.tsx' },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['src/test/setup.ts'],
  },
});
