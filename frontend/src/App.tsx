import React, { useCallback, useEffect, useState } from 'react';
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom';
import { MotionConfig } from 'framer-motion';
import { api } from './api';
import { User } from './types';
import { Button, ToastProvider } from './components/ui';
import { PublicLayout } from './components/public/PublicLayout';
import { AppShell } from './components/app/AppShell';
import { HomePage } from './pages/public/HomePage';
import {
  AboutPage,
  AiAutomationPage,
  AnalyticsSolutionsPage,
  CrmSolutionsPage,
  InventorySolutionsPage,
  OrdersSolutionsPage,
  PlatformOverviewPage,
  SecurityPublicPage,
  SmeSolutionsPage,
  WorkspaceSolutionsPage,
} from './pages/public/SolutionsAndPlatformPages';
import {
  ContactPage,
  EarlyAccessPage,
  PricingPage,
  PrivacyPolicyPage,
  TermsOfServicePage,
} from './pages/public/CommercialAndLegalPages';
import {
  AcceptInvitePage,
  ForgotPasswordPage,
  LoginPage,
  RegisterPage,
  ResetPasswordPage,
  VerifyEmailPage,
} from './pages/public/AuthPages';
import {
  IntelligencePage,
  OverviewPulsePage,
} from './pages/app/OverviewAndIntelligence';
import { CrmHubPage, CustomersPage, LeadsPage } from './pages/app/CrmPages';
import { InventoryPage, OrdersPage, ProductsPage } from './pages/app/OperationsPages';
import {
  AnalyticsPage,
  NotificationsPage,
  ReportsPage,
  TasksPage,
  TeamPage,
} from './pages/app/InsightsAndTeamPages';
import {
  AutomationPage,
  IntegrationsPage,
  SecurityPage,
  SettingsPage,
} from './pages/app/GovernanceAndAutomationPages';

const ScrollToTop: React.FC = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

interface AppRouterProps {
  initialUser?: User | null;
}

export const NexoraRoutes: React.FC<{
  user: User | null;
  authReady: boolean;
  onAuthenticated: (u: User) => void;
  onRefreshUser: () => Promise<void>;
  onLoggedOut: () => void;
}> = ({ user, authReady, onAuthenticated, onRefreshUser, onLoggedOut }) => {
  const ProtectedApp: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    if (!authReady) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#F6F8FC] text-sm text-[#4E5D78]">
          Loading NEXORA workspace session...
        </div>
      );
    }
    if (!user) {
      return <Navigate to="/login" replace />;
    }
    return (
      <AppShell user={user} onRefreshUser={onRefreshUser} onLoggedOut={onLoggedOut}>
        {children}
      </AppShell>
    );
  };

  return (
    <Routes>
      {/* Experience A: 18 Public Corporate Website Routes + Account Token Pages */}
      <Route path="/" element={<PublicLayout><HomePage /></PublicLayout>} />
      <Route path="/about" element={<PublicLayout><AboutPage /></PublicLayout>} />
      <Route path="/platform" element={<PublicLayout><PlatformOverviewPage /></PublicLayout>} />
      <Route path="/ai-automation" element={<PublicLayout><AiAutomationPage /></PublicLayout>} />
      <Route path="/solutions/crm" element={<PublicLayout><CrmSolutionsPage /></PublicLayout>} />
      <Route path="/solutions/orders" element={<PublicLayout><OrdersSolutionsPage /></PublicLayout>} />
      <Route path="/solutions/inventory" element={<PublicLayout><InventorySolutionsPage /></PublicLayout>} />
      <Route path="/solutions/analytics" element={<PublicLayout><AnalyticsSolutionsPage /></PublicLayout>} />
      <Route path="/solutions/workspace" element={<PublicLayout><WorkspaceSolutionsPage /></PublicLayout>} />
      <Route path="/security" element={<PublicLayout><SecurityPublicPage /></PublicLayout>} />
      <Route path="/solutions/smes" element={<PublicLayout><SmeSolutionsPage /></PublicLayout>} />
      <Route path="/pricing" element={<PublicLayout><PricingPage /></PublicLayout>} />
      <Route path="/contact" element={<PublicLayout><ContactPage /></PublicLayout>} />
      <Route path="/early-access" element={<PublicLayout><EarlyAccessPage /></PublicLayout>} />
      <Route path="/privacy" element={<PublicLayout><PrivacyPolicyPage /></PublicLayout>} />
      <Route path="/terms" element={<PublicLayout><TermsOfServicePage /></PublicLayout>} />

      <Route
        path="/login"
        element={
          user ? (
            <Navigate to="/app" replace />
          ) : (
            <PublicLayout>
              <LoginPage onAuthenticated={onAuthenticated} />
            </PublicLayout>
          )
        }
      />
      <Route
        path="/register"
        element={
          user ? (
            <Navigate to="/app" replace />
          ) : (
            <PublicLayout>
              <RegisterPage onAuthenticated={onAuthenticated} />
            </PublicLayout>
          )
        }
      />
      <Route path="/forgot-password" element={<PublicLayout><ForgotPasswordPage /></PublicLayout>} />
      <Route path="/reset-password" element={<PublicLayout><ResetPasswordPage /></PublicLayout>} />
      <Route path="/verify-email" element={<PublicLayout><VerifyEmailPage /></PublicLayout>} />
      <Route
        path="/accept-invite"
        element={
          <PublicLayout>
            <AcceptInvitePage onAuthenticated={onAuthenticated} />
          </PublicLayout>
        }
      />

      {/* Experience B: 17 Private Authenticated Enterprise App Routes */}
      <Route path="/app" element={<ProtectedApp>{user && <OverviewPulsePage user={user} />}</ProtectedApp>} />
      <Route path="/app/intelligence" element={<ProtectedApp>{user && <IntelligencePage user={user} />}</ProtectedApp>} />
      <Route path="/app/crm" element={<ProtectedApp>{user && <CrmHubPage user={user} />}</ProtectedApp>} />
      <Route path="/app/customers" element={<ProtectedApp>{user && <CustomersPage user={user} />}</ProtectedApp>} />
      <Route path="/app/leads" element={<ProtectedApp>{user && <LeadsPage user={user} />}</ProtectedApp>} />
      <Route path="/app/orders" element={<ProtectedApp>{user && <OrdersPage user={user} />}</ProtectedApp>} />
      <Route path="/app/products" element={<ProtectedApp>{user && <ProductsPage user={user} />}</ProtectedApp>} />
      <Route path="/app/inventory" element={<ProtectedApp>{user && <InventoryPage user={user} />}</ProtectedApp>} />
      <Route path="/app/automation" element={<ProtectedApp>{user && <AutomationPage user={user} />}</ProtectedApp>} />
      <Route path="/app/analytics" element={<ProtectedApp>{user && <AnalyticsPage user={user} />}</ProtectedApp>} />
      <Route path="/app/tasks" element={<ProtectedApp>{user && <TasksPage user={user} />}</ProtectedApp>} />
      <Route path="/app/notifications" element={<ProtectedApp>{user && <NotificationsPage user={user} />}</ProtectedApp>} />
      <Route path="/app/team" element={<ProtectedApp>{user && <TeamPage user={user} />}</ProtectedApp>} />
      <Route path="/app/reports" element={<ProtectedApp>{user && <ReportsPage user={user} />}</ProtectedApp>} />
      <Route path="/app/integrations" element={<ProtectedApp>{user && <IntegrationsPage user={user} />}</ProtectedApp>} />
      <Route
        path="/app/settings"
        element={<ProtectedApp>{user && <SettingsPage user={user} onRefreshUser={onRefreshUser} />}</ProtectedApp>}
      />
      <Route
        path="/app/security"
        element={<ProtectedApp>{user && <SecurityPage user={user} onRefreshUser={onRefreshUser} />}</ProtectedApp>}
      />

      <Route
        path="*"
        element={
          <PublicLayout>
            <div className="max-w-lg mx-auto px-4 py-24 text-center space-y-4">
              <h1 className="font-heading text-3xl font-extrabold text-[#202B43]">Page not found</h1>
              <p className="text-sm text-[#4E5D78]">The route you requested does not exist on NEXORA.</p>
              <Link to="/">
                <Button variant="primary">Return Home</Button>
              </Link>
            </div>
          </PublicLayout>
        }
      />
    </Routes>
  );
};

export function App({ initialUser }: AppRouterProps = {}) {
  const [user, setUser] = useState<User | null>(initialUser ?? null);
  const [authReady, setAuthReady] = useState<boolean>(initialUser !== undefined);

  const refreshUser = useCallback(async () => {
    try {
      const me = await api.getMe();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setAuthReady(true);
    }
  }, []);

  useEffect(() => {
    if (initialUser === undefined) {
      refreshUser();
    }
  }, [initialUser, refreshUser]);

  return (
    <MotionConfig reducedMotion="user">
      <ToastProvider>
        <BrowserRouter>
          <ScrollToTop />
          <NexoraRoutes
            user={user}
            authReady={authReady}
            onAuthenticated={(u) => {
              setUser(u);
              setAuthReady(true);
            }}
            onRefreshUser={refreshUser}
            onLoggedOut={() => setUser(null)}
          />
        </BrowserRouter>
      </ToastProvider>
    </MotionConfig>
  );
}
export default App;
