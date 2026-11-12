import React, { useEffect, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Activity,
  Sparkles,
  Briefcase,
  Users,
  Target,
  ShoppingCart,
  Package,
  Boxes,
  Workflow,
  BarChart3,
  CheckSquare,
  Bell,
  UsersRound,
  FileSpreadsheet,
  Plug,
  Settings,
  ShieldCheck,
  Search,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Building,
} from 'lucide-react';
import { NexoraLogo, Badge, Button } from '../ui';
import { User } from '../../types';
import { api } from '../../api';

export const APP_NAV_GROUPS = [
  {
    group: 'Core',
    items: [
      { label: 'Overview', to: '/app', icon: Activity, end: true },
      { label: 'AI Intelligence', to: '/app/intelligence', icon: Sparkles },
    ],
  },
  {
    group: 'CRM & Sales',
    items: [
      { label: 'CRM', to: '/app/crm', icon: Briefcase },
      { label: 'Customers', to: '/app/customers', icon: Users },
      { label: 'Leads', to: '/app/leads', icon: Target },
    ],
  },
  {
    group: 'Operations',
    items: [
      { label: 'Orders', to: '/app/orders', icon: ShoppingCart },
      { label: 'Products', to: '/app/products', icon: Package },
      { label: 'Inventory', to: '/app/inventory', icon: Boxes },
      { label: 'Automation', to: '/app/automation', icon: Workflow },
    ],
  },
  {
    group: 'Insights & Team',
    items: [
      { label: 'Analytics', to: '/app/analytics', icon: BarChart3 },
      { label: 'Tasks', to: '/app/tasks', icon: CheckSquare },
      { label: 'Notifications', to: '/app/notifications', icon: Bell },
      { label: 'Team', to: '/app/team', icon: UsersRound },
      { label: 'Reports', to: '/app/reports', icon: FileSpreadsheet },
    ],
  },
  {
    group: 'Administration',
    items: [
      { label: 'Integrations', to: '/app/integrations', icon: Plug },
      { label: 'Settings', to: '/app/settings', icon: Settings },
      { label: 'Security', to: '/app/security', icon: ShieldCheck },
    ],
  },
];

interface AppShellProps {
  user: User;
  onRefreshUser: () => Promise<void>;
  onLoggedOut: () => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ user, onRefreshUser, onLoggedOut, children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    api.listNotifications()
      .then((rows) => setUnreadCount(rows.filter((r) => !r.is_read).length))
      .catch(() => {});
  }, [location.pathname]);

  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setSearchResults(null);
      return;
    }
    const timer = setTimeout(() => {
      api.globalSearch(trimmed).then(setSearchResults).catch(() => setSearchResults(null));
    }, 200);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const currentNavLabel =
    APP_NAV_GROUPS.flatMap((g) => g.items).find((i) =>
      i.end ? location.pathname === i.to : location.pathname.startsWith(i.to)
    )?.label || 'Overview';

  const handleSwitchTenant = async (tenantId: string) => {
    if (tenantId === user.tenant.id) return;
    await api.switchWorkspace(tenantId);
    await onRefreshUser();
    navigate('/app');
  };

  const handleLogout = async () => {
    await api.logout();
    onLoggedOut();
    navigate('/login');
  };

  const SidebarContent = (
    <div className="flex flex-col h-full">
      <div className="px-4 py-4 border-b border-[#E2E8F4] flex items-center justify-between">
        <Link to="/" title="Return to Public Site">
          <NexoraLogo />
        </Link>
        <button
          type="button"
          className="lg:hidden p-1.5 rounded-lg hover:bg-[#EEF2FA] cursor-pointer"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="px-3 py-3 border-b border-[#E2E8F4] bg-[#F6F8FC]/80">
        <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-[#4E5D78] mb-1">
          <Building className="w-3.5 h-3.5 text-[#3867E9]" />
          <span>Active Workspace</span>
        </div>
        <select
          aria-label="Switch workspace"
          value={user.tenant.id}
          onChange={(e) => handleSwitchTenant(e.target.value)}
          className="w-full text-xs font-semibold px-2.5 py-2 rounded-xl bg-white border border-[#E2E8F4] text-[#202B43]"
        >
          {user.workspaces.map((w) => (
            <option key={w.tenant_id} value={w.tenant_id}>
              {w.tenant_name} ({w.role_code})
            </option>
          ))}
        </select>
        {user.tenant.is_sample && (
          <div className="mt-1.5">
            <Badge tone="warning">Sample Evaluation Data</Badge>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5" aria-label="Workspace navigation">
        {APP_NAV_GROUPS.map((grp) => (
          <div key={grp.group} className="space-y-1">
            <div className="px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-[#5E6D87]">
              {grp.group}
            </div>
            {grp.items.map((item) => {
              const Icon = item.icon;
              const isAiNav = item.to === '/app/intelligence' || item.to === '/app/automation';
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-150 ${
                      isActive
                        ? isAiNav
                          ? 'bg-[#E6F6F3] text-[#127466] border border-[#99DDD2]'
                          : 'bg-[#EAF0FE] text-[#2952C8] border border-[#C5D5FA]'
                        : 'text-[#4E5D78] hover:bg-[#EEF2FA] hover:text-[#202B43] border border-transparent'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span className="flex items-center gap-2.5">
                        <Icon
                          className={`w-4 h-4 ${
                            isActive
                              ? isAiNav
                                ? 'text-[#22A995]'
                                : 'text-[#3867E9]'
                              : isAiNav
                              ? 'text-[#22A995]'
                              : 'text-[#4E5D78]'
                          }`}
                        />
                        <span>{item.label}</span>
                      </span>
                      {item.label === 'Notifications' && unreadCount > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-[#3867E9] text-white">
                          {unreadCount}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="p-3 border-t border-[#E2E8F4] bg-[#F6F8FC] flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-bold text-[#202B43] truncate">{user.full_name}</div>
          <div className="text-[11px] text-[#4E5D78] truncate">
            {user.role_code.toUpperCase()} · {user.email}
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          title="Sign out"
          aria-label="Sign out"
          className="p-2 rounded-xl bg-white border border-[#E2E8F4] text-[#4E5D78] hover:text-[#991B1B] cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-[#F6F8FC] text-[#202B43]">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 bg-white border-r border-[#E2E8F4] sticky top-0 h-screen">
        {SidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-[#202B43]/45" onClick={() => setSidebarOpen(false)} />
          <aside className="relative z-10 w-72 bg-white h-full border-r border-[#E2E8F4]">
            {SidebarContent}
          </aside>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 h-16 bg-white/95 backdrop-blur-md border-b border-[#E2E8F4] px-4 sm:px-6 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation menu"
              className="lg:hidden p-2 rounded-xl border border-[#E2E8F4] bg-[#F6F8FC] cursor-pointer"
            >
              <Menu className="w-4 h-4" />
            </button>

            <nav className="flex items-center gap-1.5 text-xs text-[#4E5D78]" aria-label="Breadcrumb">
              <Link to="/app" className="hover:text-[#202B43] font-medium">
                {user.tenant.name}
              </Link>
              <ChevronRight className="w-3.5 h-3.5" />
              <span className="font-bold text-[#202B43] truncate">{currentNavLabel}</span>
            </nav>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="relative hidden md:block w-64">
              <Search className="w-4 h-4 text-[#5E6D87] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="search"
                aria-label="Global workspace search"
                placeholder="Search customers, orders, SKUs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] text-xs focus:bg-white focus:border-[#3867E9] focus:outline-none"
              />
              {searchResults && (
                <div className="absolute right-0 mt-1.5 w-80 bg-white border border-[#E2E8F4] rounded-2xl shadow-elevated p-2 space-y-2 z-50">
                  {(['customers', 'orders', 'products', 'leads'] as const).map((bucket) =>
                    searchResults[bucket]?.length ? (
                      <div key={bucket}>
                        <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-[#5E6D87]">
                          {bucket}
                        </div>
                        {searchResults[bucket].map((hit: any) => (
                          <button
                            key={hit.id}
                            type="button"
                            onClick={() => {
                              setSearchQuery('');
                              setSearchResults(null);
                              navigate(hit.route);
                            }}
                            className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-[#F6F8FC] text-xs flex justify-between cursor-pointer"
                          >
                            <span className="font-semibold text-[#202B43]">{hit.title}</span>
                            <span className="text-[#4E5D78]">{hit.subtitle}</span>
                          </button>
                        ))}
                      </div>
                    ) : null
                  )}
                  {!searchResults.customers?.length &&
                    !searchResults.orders?.length &&
                    !searchResults.products?.length &&
                    !searchResults.leads?.length && (
                      <div className="px-3 py-2 text-xs text-[#4E5D78]">No matching workspace records.</div>
                    )}
                </div>
              )}
            </div>

            <Link
              to="/app/notifications"
              className="relative p-2 rounded-xl border border-[#E2E8F4] bg-[#F6F8FC] hover:bg-[#EEF2FA]"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4 text-[#3867E9]" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#3867E9] text-white text-[10px] font-bold flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </Link>

            <Link to="/app/intelligence" className="hidden sm:inline-block">
              <Button variant="mint" size="sm" leftIcon={<Sparkles className="w-3.5 h-3.5 text-[#22A995]" />}>
                Ask AI
              </Button>
            </Link>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};
