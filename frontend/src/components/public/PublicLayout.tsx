import React, { useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronDown, Menu, X, ShieldCheck, ArrowRight } from 'lucide-react';
import { NexoraLogo, Button } from '../ui';

const SOLUTION_LINKS = [
  { label: 'CRM Solutions', to: '/solutions/crm', desc: 'Customers, contacts, leads & follow-up timelines' },
  { label: 'Order Management', to: '/solutions/orders', desc: 'Create, approve & track orders with GST support' },
  { label: 'Inventory Management', to: '/solutions/inventory', desc: 'SKUs, stock ledger, suppliers & atomic locks' },
  { label: 'Business Analytics', to: '/solutions/analytics', desc: 'Real-data trends, revenue & operational health' },
  { label: 'Workspace & Collaboration', to: '/solutions/workspace', desc: 'Tasks, team activity, alerts & permissions' },
  { label: 'AI & Automation', to: '/ai-automation', desc: 'Grounded Gemini copilot & rule-based workflows' },
  { label: 'Solutions for SMEs', to: '/solutions/smes', desc: 'Built for India distributors, retail & B2B teams' },
];

export const PublicLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [solutionsOpen, setSolutionsOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-[#F6F8FC] text-[#202B43]">
      <a
        href="#public-main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:rounded-xl focus:bg-[#3867E9] focus:text-white focus:font-semibold"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-[#E2E8F4] bg-[#F6F8FC]/95 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 py-3 flex items-center justify-between gap-4">
          <Link to="/" onClick={() => setMobileOpen(false)} aria-label="NEXORA Home">
            <NexoraLogo />
          </Link>

          <nav className="hidden lg:flex items-center gap-1" aria-label="Primary navigation">
            <NavLink
              to="/platform"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-medium transition-colors ${
                  isActive ? 'bg-[#EAF0FE] text-[#3867E9] font-semibold' : 'text-[#4E5D78] hover:text-[#202B43] hover:bg-white/70'
                }`
              }
            >
              Platform
            </NavLink>

            <div
              className="relative"
              onMouseEnter={() => setSolutionsOpen(true)}
              onMouseLeave={() => setSolutionsOpen(false)}
            >
              <button
                type="button"
                aria-expanded={solutionsOpen}
                onClick={() => setSolutionsOpen((v) => !v)}
                className={`inline-flex items-center gap-1 px-3.5 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer ${
                  location.pathname.startsWith('/solutions') || location.pathname === '/ai-automation'
                    ? 'bg-[#EAF0FE] text-[#3867E9] font-semibold'
                    : 'text-[#4E5D78] hover:text-[#202B43] hover:bg-white/70'
                }`}
              >
                <span>Solutions</span>
                <ChevronDown className={`w-4 h-4 transition-transform ${solutionsOpen ? 'rotate-180' : ''}`} />
              </button>

              {solutionsOpen && (
                <div className="absolute left-0 top-full pt-2 w-[360px]">
                  <div className="bg-white border border-[#E2E8F4] rounded-2xl shadow-elevated p-2 space-y-0.5">
                    {SOLUTION_LINKS.map((item) => (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={() => setSolutionsOpen(false)}
                        className="block px-3.5 py-2.5 rounded-xl hover:bg-[#F6F8FC] transition-colors"
                      >
                        <div className="text-sm font-semibold text-[#202B43]">{item.label}</div>
                        <div className="text-xs text-[#4E5D78]">{item.desc}</div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <NavLink
              to="/security"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-medium transition-colors ${
                  isActive ? 'bg-[#EAF0FE] text-[#3867E9] font-semibold' : 'text-[#4E5D78] hover:text-[#202B43] hover:bg-white/70'
                }`
              }
            >
              Security
            </NavLink>

            <NavLink
              to="/pricing"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-medium transition-colors ${
                  isActive ? 'bg-[#EAF0FE] text-[#3867E9] font-semibold' : 'text-[#4E5D78] hover:text-[#202B43] hover:bg-white/70'
                }`
              }
            >
              Pricing
            </NavLink>

            <NavLink
              to="/about"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-medium transition-colors ${
                  isActive ? 'bg-[#EAF0FE] text-[#3867E9] font-semibold' : 'text-[#4E5D78] hover:text-[#202B43] hover:bg-white/70'
                }`
              }
            >
              About
            </NavLink>
          </nav>

          <div className="hidden lg:flex items-center gap-2.5">
            <Link to="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link to="/register">
              <Button variant="secondary" size="sm">Create workspace</Button>
            </Link>
            <Link to="/early-access">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Early access
              </Button>
            </Link>
          </div>

          <button
            type="button"
            className="lg:hidden p-2 rounded-xl border border-[#E2E8F4] bg-white text-[#202B43] cursor-pointer"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
            onClick={() => setMobileOpen((v) => !v)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="lg:hidden border-t border-[#E2E8F4] bg-white px-4 py-4 space-y-3">
            <div className="grid grid-cols-1 gap-1">
              <Link to="/platform" onClick={() => setMobileOpen(false)} className="px-3 py-2 rounded-xl text-sm font-semibold hover:bg-[#F6F8FC]">
                Platform Overview
              </Link>
              {SOLUTION_LINKS.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className="px-3 py-2 rounded-xl text-sm text-[#4E5D78] hover:bg-[#F6F8FC] hover:text-[#202B43]"
                >
                  {item.label}
                </Link>
              ))}
              <Link to="/security" onClick={() => setMobileOpen(false)} className="px-3 py-2 rounded-xl text-sm font-semibold hover:bg-[#F6F8FC]">
                Security &amp; Privacy
              </Link>
              <Link to="/pricing" onClick={() => setMobileOpen(false)} className="px-3 py-2 rounded-xl text-sm font-semibold hover:bg-[#F6F8FC]">
                Pricing
              </Link>
              <Link to="/about" onClick={() => setMobileOpen(false)} className="px-3 py-2 rounded-xl text-sm font-semibold hover:bg-[#F6F8FC]">
                About NEXORA
              </Link>
              <Link to="/contact" onClick={() => setMobileOpen(false)} className="px-3 py-2 rounded-xl text-sm font-semibold hover:bg-[#F6F8FC]">
                Contact
              </Link>
            </div>
            <div className="pt-2 border-t border-[#E2E8F4] flex flex-col gap-2">
              <Link to="/login" onClick={() => setMobileOpen(false)}>
                <Button variant="secondary" className="w-full">Sign in to Workspace</Button>
              </Link>
              <Link to="/register" onClick={() => setMobileOpen(false)}>
                <Button variant="primary" className="w-full">Register Business Workspace</Button>
              </Link>
              <Link to="/early-access" onClick={() => setMobileOpen(false)}>
                <Button variant="lime" className="w-full">Request Early Access</Button>
              </Link>
            </div>
          </div>
        )}
      </header>

      <main id="public-main" className="flex-1">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
        >
          {children}
        </motion.div>
      </main>

      <footer className="bg-white border-t border-[#E2E8F4] text-[#202B43] mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 pb-12 border-b border-[#E2E8F4]">
            <div className="lg:col-span-2 space-y-4">
              <div className="inline-flex items-center gap-2.5">
                <span className="w-9 h-9 rounded-xl bg-[#3867E9] flex items-center justify-center shadow-sm border border-[#2952C8]">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none">
                    <path d="M6.5 18.5V5.5L17.5 18.5V5.5" stroke="#FFFFFF" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <div>
                  <div className="font-heading text-lg font-extrabold text-[#202B43] tracking-tight">NEXORA</div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#3867E9]">
                    The Next Generation Business Developer
                  </div>
                </div>
              </div>
              <p className="text-sm text-[#4E5D78] max-w-md leading-relaxed">
                One intelligent workspace to help growing businesses manage relationships, daily operations, orders, inventory, analytics and human-approved automation. Built for Indian SMEs first; engineered for global scale.
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F6F8FC] border border-[#E2E8F4] text-xs text-[#127466] font-medium">
                <ShieldCheck className="w-4 h-4 text-[#22A995]" />
                <span>PostgreSQL RLS + Argon2id + Human-in-Control AI</span>
              </div>
            </div>

            <div className="space-y-2.5 text-sm">
              <h3 className="font-heading text-xs font-bold uppercase tracking-wider text-[#202B43] mb-3">Platform</h3>
              <Link to="/" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Home</Link>
              <Link to="/platform" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Platform overview</Link>
              <Link to="/ai-automation" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">AI and automation</Link>
              <Link to="/security" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Security &amp; privacy</Link>
              <Link to="/pricing" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Pricing</Link>
            </div>

            <div className="space-y-2.5 text-sm">
              <h3 className="font-heading text-xs font-bold uppercase tracking-wider text-[#202B43] mb-3">Solutions</h3>
              <Link to="/solutions/crm" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">CRM solutions</Link>
              <Link to="/solutions/orders" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Order management</Link>
              <Link to="/solutions/inventory" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Inventory management</Link>
              <Link to="/solutions/analytics" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Business analytics</Link>
              <Link to="/solutions/workspace" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Workspace &amp; collaboration</Link>
              <Link to="/solutions/smes" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Solutions for SMEs</Link>
            </div>

            <div className="space-y-2.5 text-sm">
              <h3 className="font-heading text-xs font-bold uppercase tracking-wider text-[#202B43] mb-3">Company &amp; Access</h3>
              <Link to="/about" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">About NEXORA</Link>
              <Link to="/contact" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Contact</Link>
              <Link to="/early-access" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Early access</Link>
              <Link to="/login" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Login</Link>
              <Link to="/register" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Registration</Link>
              <Link to="/privacy" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Privacy policy</Link>
              <Link to="/terms" className="block text-[#4E5D78] hover:text-[#3867E9] transition-colors">Terms of service</Link>
            </div>
          </div>

          <div className="pt-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-[#5E6D87]">
            <div>© {new Date().getFullYear()} NEXORA. Engineered for multi-tenant operational reliability.</div>
            <div>Sample demonstration figures on this website use fictional records and are explicitly labeled.</div>
          </div>
        </div>
      </footer>
    </div>
  );
};
