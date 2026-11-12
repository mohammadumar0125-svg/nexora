import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ShieldCheck,
  Users,
  ShoppingCart,
  Boxes,
  BarChart3,
  CheckSquare,
  Sparkles,
  Building2,
  Database,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { Badge, Button, Card } from '../../components/ui';
import { EcosystemSyncPreview } from '../../components/public/EcosystemSyncPreview';

interface SectionSpec {
  title: string;
  desc: string;
}

interface MarketingTemplateProps {
  badge: string;
  headline: string;
  subtitle: string;
  highlights: SectionSpec[];
  architectureNote: string;
  icon: React.ReactNode;
}

const MarketingPageTemplate: React.FC<MarketingTemplateProps> = ({
  badge,
  headline,
  subtitle,
  highlights,
  architectureNote,
  icon,
}) => {
  const isAi = badge.toLowerCase().includes('ai');
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-16">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-7 space-y-5">
          <Badge tone={isAi ? 'mint' : 'cobalt'}>{badge}</Badge>
          <h1 className="font-heading text-3xl sm:text-5xl font-extrabold text-[#202B43] leading-tight">
            {headline}
          </h1>
          <p className="text-base sm:text-lg text-[#4E5D78] leading-relaxed">{subtitle}</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link to="/register">
              <Button variant="primary" size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Start Workspace
              </Button>
            </Link>
            <Link to="/early-access">
              <Button variant="secondary" size="lg">Request Guided Pilot</Button>
            </Link>
          </div>
        </div>
        <Card accent={isAi ? 'mint' : 'cobalt'} className="lg:col-span-5 space-y-4 bg-white">
          <div
            className={`w-11 h-11 rounded-xl flex items-center justify-center ${
              isAi ? 'bg-[#E6F6F3] text-[#22A995]' : 'bg-[#EAF0FE] text-[#3867E9]'
            }`}
          >
            {icon}
          </div>
          <div className="font-heading text-lg font-bold text-[#202B43]">Operational Design Guarantee</div>
          <p className="text-sm text-[#4E5D78] leading-relaxed">{architectureNote}</p>
          <div
            className={`pt-2 border-t border-[#E2E8F4] flex items-center justify-between text-xs font-semibold ${
              isAi ? 'text-[#127466]' : 'text-[#3867E9]'
            }`}
          >
            <span>Tenant-isolated PostgreSQL model</span>
            <Link to="/login" className="underline">Try live workspace</Link>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {highlights.map((h) => (
          <Card key={h.title} accent={isAi ? 'mint' : 'cobalt'} className="space-y-2.5">
            <h2 className="font-heading text-lg font-bold text-[#202B43]">{h.title}</h2>
            <p className="text-sm text-[#4E5D78] leading-relaxed">{h.desc}</p>
          </Card>
        ))}
      </div>
    </div>
  );
};

export const AboutPage: React.FC = () => (
  <MarketingPageTemplate
    badge="About NEXORA"
    headline="Built for growing businesses ready to operate on one source of truth"
    subtitle="NEXORA — The Next Generation Business Developer — brings enterprise-grade relationship management, transactional operations, inventory reliability and human-controlled AI into a calm workspace practical enough for everyday SME teams."
    icon={<Building2 className="w-5 h-5" />}
    architectureNote="Started with deep operational study of Indian wholesalers and SME teams who run revenue inside messaging apps and spreadsheets, NEXORA is architected from day one for clean multi-tenant internationalization."
    highlights={[
      { title: 'Customer & Operations Unity', desc: 'Sales teams, clerks, warehouse managers and founders read and update the same real-time entity records.' },
      { title: 'Honesty & Reliability First', desc: 'Zero inflated vanity claims. Analytics reflect authorized database rows; AI cites its source tables cleanly.' },
      { title: 'India First, Global Capable', desc: 'GST fields, Indian currency precision and mobile responsiveness built natively alongside international architecture.' },
    ]}
  />
);

export const PlatformOverviewPage: React.FC = () => (
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-12">
    <div className="max-w-3xl space-y-4">
      <Badge tone="forest">Platform Overview</Badge>
      <h1 className="font-heading text-3xl sm:text-5xl font-extrabold text-[#202B43]">
        Six connected modules over one secure multi-tenant schema
      </h1>
      <p className="text-base sm:text-lg text-[#4E5D78] leading-relaxed">
        Instead of gluing brittle spreadsheets onto standalone CRM and billing tools, NEXORA models users, tenants, customers, leads, orders, stock movements, tasks, workflows and AI audit trails in one relational PostgreSQL core.
      </p>
    </div>
    <EcosystemSyncPreview />
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {[
        { title: 'Shared API & RBAC Layer', desc: 'FastAPI routes enforce authentication, session cookies, CSRF validation, tenant checks and least-privilege roles.' },
        { title: 'Atomic Postgres Transactions', desc: 'Order approvals lock affected inventory rows (`SELECT FOR UPDATE`), insert immutable stock ledger records and reject negative stock.' },
        { title: 'Modular Adapters', desc: 'Email, messaging, payments, cloud storage and Google Gemini run behind clean server-side boundaries.' },
      ].map((c) => (
        <Card key={c.title} accent="forest" className="space-y-2">
          <Database className="w-5 h-5 text-[#3867E9]" />
          <h2 className="font-heading text-lg font-bold text-[#202B43]">{c.title}</h2>
          <p className="text-sm text-[#4E5D78] leading-relaxed">{c.desc}</p>
        </Card>
      ))}
    </div>
  </div>
);

export const AiAutomationPage: React.FC = () => (
  <MarketingPageTemplate
    badge="AI & Automation"
    headline="NEXORA Intelligence: grounded insights with people strictly in control"
    subtitle="Powered by server-side Google Gemini integration with structured SQL grounding, prompt injection barriers and mandatory human approval before any customer message or state change is dispatched."
    icon={<Sparkles className="w-5 h-5" />}
    architectureNote="Every AI query executes strictly within the authenticated tenant's authorized dataset. External text is never trusted as system instruction, API keys remain exclusively on the backend, and consequential actions wait in an approval queue."
    highlights={[
      { title: 'Operational Q&A', desc: 'Ask which orders are delayed, which products have low stock or which customers need follow-up with source links.' },
      { title: 'Order Intake Extraction', desc: 'Parse messy mixed-language WhatsApp text into structured draft line items mapped to verified SKUs.' },
      { title: 'Safeguarded Automation', desc: 'Define triggers and conditions with execution history logs, retries and human approval checkpoints.' },
    ]}
  />
);

export const CrmSolutionsPage: React.FC = () => (
  <MarketingPageTemplate
    badge="CRM Solutions"
    headline="Every customer account, contact, lead and conversation in one place"
    subtitle="Track leads from initial enquiry through qualified opportunities to repeat customer accounts without losing context across team handoffs."
    icon={<Users className="w-5 h-5" />}
    architectureNote="Supports B2B customer accounts, multi-contact directories, lead stages, follow-up scheduling, notes, activity timelines and role-checked CSV import/export."
    highlights={[
      { title: '360° Customer Timeline', desc: 'See notes, calls, orders, follow-ups and owner assignments on every customer record.' },
      { title: 'Lead Pipeline Management', desc: 'Organize active leads by stage, value, owner and next action date with fast filtering.' },
      { title: 'Follow-Up Discipline', desc: 'Schedule due dates and surface overdue accounts directly on each user’s Business Pulse.' },
    ]}
  />
);

export const OrdersSolutionsPage: React.FC = () => (
  <MarketingPageTemplate
    badge="Order Management"
    headline="Structured orders connected directly to customer balances and stock"
    subtitle="Create, review, approve and print orders in seconds while PostgreSQL validates tax, discounts and inventory availability atomically."
    icon={<ShoppingCart className="w-5 h-5" />}
    architectureNote="Supports draft order creation (manual or AI-parsed from customer messages), tax/discount calculation, status transitions, printable summaries and transactional stock reservation."
    highlights={[
      { title: 'End-to-End Lifecycle', desc: 'Track Draft, Confirmed, Packed, Shipped, Delivered and Cancelled states with timestamps.' },
      { title: 'Pending Order Alerts', desc: 'Automatically flag orders waiting on approval or overdue against fulfilment expectations.' },
      { title: 'Printable Order Summaries', desc: 'Clean print-ready order & GST invoice layouts alongside CSV/JSON exports.' },
    ]}
  />
);

export const InventorySolutionsPage: React.FC = () => (
  <MarketingPageTemplate
    badge="Inventory Management"
    headline="Zero negative stock. Full movement history across every SKU."
    subtitle="Manage SKUs, suppliers, low-stock reorder thresholds, unit conversions and stock valuation using concurrency-safe SQL locks."
    icon={<Boxes className="w-5 h-5" />}
    architectureNote="All quantity additions, manual adjustments and order deductions write immutable rows into `stock_movements`, protected by database constraints and row-level locks."
    highlights={[
      { title: 'Movement Ledger', desc: 'Every unit change is traced to its operator, reason, order reference and before/after count.' },
      { title: 'Reorder & Low-Stock Alerts', desc: 'Custom per-SKU reorder levels feed directly into Business Pulse alerts and AI briefs.' },
      { title: 'Supplier Directory', desc: 'Link products to preferred suppliers with lead-time notes and cost valuation.' },
    ]}
  />
);

export const AnalyticsSolutionsPage: React.FC = () => (
  <MarketingPageTemplate
    badge="Business Analytics"
    headline="Live metrics computed from real operational records — never guesswork"
    subtitle="Inspect revenue, order volume, pipeline conversion, stock health, task completion and workflow performance across date ranges."
    icon={<BarChart3 className="w-5 h-5" />}
    architectureNote="Every metric defines its calculation formula transparently, offers CSV export for finance reviews and clearly separates empty/insufficient data from confirmed metrics."
    highlights={[
      { title: 'Sales & Revenue Trends', desc: 'Track confirmed and delivered order value over configurable periods with comparison deltas.' },
      { title: 'Stock Health & Valuation', desc: 'Monitor healthy, low-stock and out-of-stock SKUs alongside total inventory valuation.' },
      { title: 'Execution & Task Velocity', desc: 'See overdue tasks, pending approvals and team activity per operator.' },
    ]}
  />
);

export const WorkspaceSolutionsPage: React.FC = () => (
  <MarketingPageTemplate
    badge="Workspace & Collaboration"
    headline="Aligned daily execution across owners, managers, sales and dispatch"
    subtitle="Replace scattered chat follow-ups with assigned tasks, priority reminders, workspace notifications and clear role permissions."
    icon={<CheckSquare className="w-5 h-5" />}
    architectureNote="Built with strict RBAC roles (Owner, Admin, Manager, Staff, Viewer), in-app notifications linked to affected entities and keyboard shortcuts for rapid navigation."
    highlights={[
      { title: 'Task & Reminder Engine', desc: 'Tie tasks directly to customers, leads or orders with due dates and completion tracking.' },
      { title: 'Notification Centre', desc: 'Real-time workspace alerts for assignments, low stock thresholds and pending approvals.' },
      { title: 'Team Governance', desc: 'Invite colleagues safely with temporary credentials, expiration controls and session revocation.' },
    ]}
  />
);

export const SecurityPublicPage: React.FC = () => (
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-12">
    <div className="max-w-3xl space-y-4">
      <Badge tone="forest">Security &amp; Privacy Architecture</Badge>
      <h1 className="font-heading text-3xl sm:text-5xl font-extrabold text-[#202B43]">
        Designed security-first around OWASP ASVS controls
      </h1>
      <p className="text-base sm:text-lg text-[#4E5D78] leading-relaxed">
        Every business record is treated as strictly confidential. Below is the verifiable control set engineered into NEXORA without overstated or unverified certification claims.
      </p>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {[
        {
          title: 'Authentication & Session Security',
          items: [
            'Argon2id password hashing (argon2-cffi RFC 9106 parameters) with timing-safe unknown user lookups',
            'Expiring single-use tokens for email verification and password reset',
            'HttpOnly, SameSite session cookies + required per-session X-CSRF-Token headers on mutations',
            'Optional TOTP Two-Factor Authentication (MFA), login rate limiting and session revocation',
          ],
        },
        {
          title: 'Tenant Isolation & Authorization',
          items: [
            'Tenant membership derived strictly from verified server-side sessions, never client-supplied headers',
            'Role-Based Access Control (RBAC) across Owner, Admin, Manager, Staff and Viewer permissions',
            'PostgreSQL Row-Level Security (FORCE ROW LEVEL SECURITY) bound to app.current_tenant_id',
            'Cross-tenant IDOR checks verified continuously in automated pytest security suites',
          ],
        },
        {
          title: 'AI Governance & Prompt Safety',
          items: [
            'Gemini API keys reside strictly in server environment variables — zero browser exposure',
            'User permissions checked prior to retrieving AI operational context',
            'Prompt-injection boundary instructions treating customer inputs as untrusted data',
            'Consequential actions require human approval and write entries to ai_interactions & audit_logs',
          ],
        },
        {
          title: 'Privacy & Regulatory Readiness (DPDP Act)',
          items: [
            'Data minimization: collect only required workspace operational fields',
            'Tenant-level portable data export and controlled account deletion safeguards',
            'Configurable data retention controls and private file storage validation',
            'DPDP Act & cross-border privacy requirements reviewed alongside qualified legal counsel prior to commercial GA',
          ],
        },
      ].map((block) => (
        <Card key={block.title} accent="forest" className="space-y-4">
          <div className="flex items-center gap-2 text-[#3867E9]">
            <Lock className="w-5 h-5" />
            <h2 className="font-heading text-lg font-bold text-[#202B43]">{block.title}</h2>
          </div>
          <ul className="space-y-2.5 text-sm text-[#4E5D78]">
            {block.items.map((pt) => (
              <li key={pt} className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#3867E9] shrink-0 mt-0.5" />
                <span>{pt}</span>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  </div>
);

export const SmeSolutionsPage: React.FC = () => (
  <MarketingPageTemplate
    badge="Solutions for SMEs"
    headline="Practical daily control for distributors, retailers and service operators"
    subtitle="Engineered around how growing businesses in India actually sell, coordinate warehouse teams and maintain customer trust — ready to expand cleanly into international markets."
    icon={<ShieldCheck className="w-5 h-5" />}
    architectureNote="Teams get started in minutes using familiar terms (customers, SKUs, orders, tasks) while gaining enterprise PostgreSQL integrity, multi-role approvals and guided AI."
    highlights={[
      { title: 'Wholesale & FMCG Distribution', desc: 'Capture informal retailer messages, confirm stock availability instantly and eliminate manual billing typos.' },
      { title: 'Multi-Outlet Retail', desc: 'Coordinate purchase suppliers, maintain reorder alerts and review SKU margin/turnover analytics.' },
      { title: 'B2B Services & Agencies', desc: 'Standardize lead pipelines, follow-up tasks and client delivery schedules across teams.' },
    ]}
  />
);
