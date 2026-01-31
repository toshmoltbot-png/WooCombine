import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.js'],
    globals: true,
    include: ['src/**/*.{test,spec}.{js,jsx}', 'src/**/__tests__/**/*.{js,jsx}'],
    exclude: ['node_modules', 'build', 'dist', 'src/utils/__tests__/optimizationTests.js'],
    coverage: {
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/**/*.test.{js,jsx}', 'src/main.jsx', 'src/firebase.js', 'src/**/__tests__/**']
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
