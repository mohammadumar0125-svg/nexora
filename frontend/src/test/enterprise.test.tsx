import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MotionConfig } from 'framer-motion';
import { ToastProvider } from '../components/ui';
import { PublicLayout } from '../components/public/PublicLayout';
import { HomePage } from '../pages/public/HomePage';
import { PricingPage } from '../pages/public/CommercialAndLegalPages';
import { LoginPage, RegisterPage } from '../pages/public/AuthPages';
import { AppShell, APP_NAV_GROUPS } from '../components/app/AppShell';
import { NexoraRoutes } from '../App';
import { User } from '../types';

const WRAP = (node: React.ReactNode, initialEntries: string[] = ['/']) => (
  <MotionConfig reducedMotion="always">
    <ToastProvider>
      <MemoryRouter initialEntries={initialEntries}>{node}</MemoryRouter>
    </ToastProvider>
  </MotionConfig>
);

const MOCK_USER: User = {
  id: 'u-1',
  email: 'owner@testcorp.example',
  full_name: 'Test Owner',
  role_code: 'owner',
  permissions: ['crm:read', 'crm:write', 'orders:read', 'analytics:read', 'security:read'],
  is_email_verified: true,
  mfa_enabled: false,
  csrf_token: 'csrf-demo',
  tenant: {
    id: 't-1',
    name: 'Test Corp Distributors',
    slug: 'test-corp-distributors',
    currency: 'INR',
    is_sample: true,
  },
  workspaces: [
    {
      tenant_id: 't-1',
      tenant_name: 'Test Corp Distributors',
      tenant_slug: 'test-corp-distributors',
      role_code: 'owner',
      is_sample: true,
    },
  ],
};

describe('NEXORA Public Corporate Website', () => {
  it('renders homepage hero copy, CTAs, interactive preview, and footer links', () => {
    render(WRAP(<PublicLayout><HomePage /></PublicLayout>));
    expect(screen.getByText(/Your entire business\. One intelligent ecosystem\./i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Explore NEXORA/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Discover the platform/i })).toBeInTheDocument();

    const expectedFooterRoutes = [
      'Home',
      'Platform overview',
      'AI and automation',
      'Pricing',
      'CRM solutions',
      'Order management',
      'Inventory management',
      'Business analytics',
      'Solutions for SMEs',
      'About NEXORA',
      'Early access',
      'Login',
      'Registration',
      'Privacy policy',
      'Terms of service',
    ];
    for (const label of expectedFooterRoutes) {
      expect(screen.getAllByText(new RegExp(label, 'i')).length).toBeGreaterThanOrEqual(1);
    }
  });

  it('renders proposed pilot-validation pricing tiers without fabricated user claims', () => {
    render(WRAP(<PublicLayout><PricingPage /></PublicLayout>, ['/pricing']));
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Growth')).toBeInTheDocument();
    expect(screen.getByText('Scale')).toBeInTheDocument();
    expect(screen.getAllByText(/PROPOSED — PILOT VALIDATION/i).length).toBe(3);
  });

  it('renders Sign In and Business Workspace Registration forms cleanly', () => {
    render(WRAP(<PublicLayout><LoginPage onAuthenticated={() => {}} /></PublicLayout>, ['/login']));
    expect(screen.getByText(/Sign in to NEXORA/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Work Email/i)).toBeInTheDocument();

    render(WRAP(<PublicLayout><RegisterPage onAuthenticated={() => {}} /></PublicLayout>, ['/register']));
    expect(screen.getByLabelText(/Business \/ Workspace Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Your Full Name/i)).toBeInTheDocument();
  });

  it('protects private /app routes by redirecting unauthenticated visitors to /login', () => {
    render(
      WRAP(
        <NexoraRoutes
          user={null}
          authReady={true}
          onAuthenticated={() => {}}
          onRefreshUser={async () => {}}
          onLoggedOut={() => {}}
        />,
        ['/app/orders']
      )
    );
    expect(screen.getByText(/Sign in to NEXORA/i)).toBeInTheDocument();
  });
});

describe('NEXORA Private Enterprise Application Navigation', () => {
  it('renders all 17 enterprise module links inside AppShell', () => {
    const allNavLabels = APP_NAV_GROUPS.flatMap((g) => g.items.map((i) => i.label));
    expect(allNavLabels).toHaveLength(17);

    render(
      WRAP(
        <AppShell user={MOCK_USER} onRefreshUser={async () => {}} onLoggedOut={() => {}}>
          <div>Workspace Child Content</div>
        </AppShell>,
        ['/app']
      )
    );

    for (const label of allNavLabels) {
      expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
    }
    expect(screen.getByText(/Sample Evaluation Data/i)).toBeInTheDocument();
  });

  it('renders all 18 public routes without runtime crashes', () => {
    const publicRoutes = [
      '/',
      '/about',
      '/platform',
      '/ai-automation',
      '/solutions/crm',
      '/solutions/orders',
      '/solutions/inventory',
      '/solutions/analytics',
      '/solutions/workspace',
      '/security',
      '/solutions/smes',
      '/pricing',
      '/contact',
      '/early-access',
      '/login',
      '/register',
      '/privacy',
      '/terms',
    ];
    for (const path of publicRoutes) {
      const { unmount } = render(
        WRAP(
          <NexoraRoutes
            user={null}
            authReady={true}
            onAuthenticated={() => {}}
            onRefreshUser={async () => {}}
            onLoggedOut={() => {}}
          />,
          [path]
        )
      );
      expect(document.body.textContent?.length).toBeGreaterThan(50);
      unmount();
    }
  });
});
