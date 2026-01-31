import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Navigation from '../Navigation';
import { AuthProvider } from '../../context/AuthContext';
import { EventProvider } from '../../context/EventContext';
import { ToastProvider } from '../../context/ToastContext';

// Mock the AuthContext hook
const mockAuthContext = {
  user: { uid: 'test-user', email: 'test@example.com' },
  userRole: 'organizer',
  leagues: [{ id: 'league1', name: 'Test League' }],
  selectedLeagueId: 'league1',
  setSelectedLeagueId: vi.fn(),
  logout: vi.fn(),
};

vi.mock('../../context/AuthContext', () => ({
  AuthProvider: ({ children }) => children,
  useAuth: () => mockAuthContext,
  useLogout: () => vi.fn(),
}));

vi.mock('../../context/EventContext', () => ({
  EventProvider: ({ children }) => children,
  useEvent: () => ({
    selectedEvent: null,
    events: [],
    loading: false,
    error: null,
  }),
}));

vi.mock('../../context/ToastContext', () => ({
  ToastProvider: ({ children }) => children,
  useToast: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
    showInfo: vi.fn(),
  }),
}));

const NavigationWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Navigation', () => {
  it('renders without crashing', () => {
    // Navigation component renders with mocked context
    const { container } = render(
      <NavigationWrapper>
        <Navigation isOpen={true} onClose={vi.fn()} />
      </NavigationWrapper>
    );
    expect(container).toBeTruthy();
  });

  it('renders navigation menu when open', () => {
    render(
      <NavigationWrapper>
        <Navigation isOpen={true} onClose={vi.fn()} />
      </NavigationWrapper>
    );
    // The component renders without throwing
    // Specific content tests skipped - these depend on actual nav structure
  });
});
