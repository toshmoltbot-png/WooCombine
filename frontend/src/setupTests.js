import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Polyfill for TextEncoder/TextDecoder
import { TextEncoder, TextDecoder } from 'util';
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Provide a minimal fetch stub for libraries that expect it
if (!global.fetch) {
  global.fetch = vi.fn(() => Promise.reject(new Error('fetch not implemented in test env')));
}

// Mock Firebase modules
vi.mock('./firebase', () => ({
  auth: {
    signInWithEmailAndPassword: vi.fn(),
    createUserWithEmailAndPassword: vi.fn(),
    signOut: vi.fn(),
    onAuthStateChanged: vi.fn(),
  },
  db: {},
}));

// Mock firebase/auth to avoid Node fetch dependency and control auth flow in tests
vi.mock('firebase/auth', () => {
  return {
    onAuthStateChanged: (_auth, callback) => {
      // Simulate next tick to avoid setState outside act warnings
      setTimeout(() => callback(null), 0);
      // Return unsubscribe function
      return () => {};
    },
    signOut: vi.fn(),
  };
});

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({
      pathname: '/',
      search: '',
      hash: '',
      state: null,
    }),
  };
});
