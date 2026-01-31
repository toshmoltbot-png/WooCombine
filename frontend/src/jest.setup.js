// This runs BEFORE any test modules are loaded
// Define import.meta.env for Vite compatibility in Jest
Object.defineProperty(globalThis, 'import', {
  value: {
    meta: {
      env: {
        VITE_API_BASE: 'http://localhost:3000/api',
        VITE_REQUIRE_ADMIN_MFA: 'false',
        PROD: false,
        DEV: true,
        MODE: 'test'
      }
    }
  },
  writable: true,
  configurable: true
});
