import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Users,
  ShoppingCart,
  Boxes,
  BarChart3,
  CheckSquare,
  Sparkles,
  ShieldCheck,
  Lock,
  Workflow,
  Clock,
  AlertCircle,
  CheckCircle2,
  Building2,
  Layers,
  Database,
} from 'lucide-react';
import { Button, Card, Badge, Input, Select, Textarea, useToast } from '../../components/ui';
import { EcosystemSyncPreview } from '../../components/public/EcosystemSyncPreview';
import { api } from '../../api';

const CAPABILITIES = [
  {
    title: 'CRM & Relationships',
    desc: 'Unified customer accounts, contacts, lead pipeline stages, follow-ups and activity timelines.',
    to: '/solutions/crm',
    icon: Users,
  },
  {
    title: 'Order Management',
    desc: 'Create, approve and track customer orders with tax, discounts, fulfilment states and printable summaries.',
    to: '/solutions/orders',
    icon: ShoppingCart,
  },
  {
    title: 'Inventory Control',
    desc: 'SKU catalogue, suppliers, low-stock alerts, movement ledger and transactional row-locked deductions.',
    to: '/solutions/inventory',
    icon: Boxes,
  },
  {
    title: 'Business Analytics',
    desc: 'Real-time sales trends, customer growth and stock valuation calculated from live PostgreSQL records.',
    to: '/solutions/analytics',
    icon: BarChart3,
  },
  {
    title: 'Workspace & Tasks',
    desc: 'Team tasks, assignments, operational notifications and role-governed workspaces.',
    to: '/solutions/workspace',
    icon: CheckSquare,
  },
  {
    title: 'AI & Automation',
    desc: 'Grounded Gemini operational Q&A, drafted follow-ups and approval-gated workflow triggers.',
    to: '/ai-automation',
    icon: Sparkles,
  },
];

const AI_SAMPLE_PROMPTS = [
  {
    q: 'Which products have low stock?',
    a: 'Sample preview: 3 active SKUs are below their reorder threshold in the sample inventory table (e.g., Cooking Oil 1L at 8 units vs threshold 20). Suggested action: create supplier restock task for Purchasing.',
    source: 'inventory + products (sample records)',
  },
  {
    q: 'Which orders are delayed?',
    a: 'Sample preview: 2 confirmed orders have crossed their target dispatch window without a shipped status update. Suggested action: notify dispatch lead and prepare customer update draft.',
    source: 'orders + tasks (sample records)',
  },
  {
    q: 'Which customers need follow-up?',
    a: 'Sample preview: 4 active accounts have open follow-up reminders scheduled today with no logged activity in the last 7 days.',
    source: 'customers + activities (sample records)',
  },
];

export const HomePage: React.FC = () => {
  const { notify } = useToast();
  const [selectedAiIdx, setSelectedAiIdx] = useState(0);
  const [selectedPulseTab, setSelectedPulseTab] = useState<'orders' | 'stock' | 'followups'>('orders');

  const [earlyForm, setEarlyForm] = useState({
    full_name: '',
    email: '',
    company_name: '',
    business_type: 'Wholesale & Distribution',
    team_size: '6-25',
    notes: '',
  });
  const [earlySubmitting, setEarlySubmitting] = useState(false);
  const [earlyDone, setEarlyDone] = useState(false);

  const submitEarlyAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    setEarlySubmitting(true);
    try {
      await api.submitEarlyAccess(earlyForm);
      setEarlyDone(true);
      notify('Early access request saved. Our team will reach out cleanly.', 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Unable to submit request.', 'error');
    } finally {
      setEarlySubmitting(false);
    }
  };

  return (
    <div className="space-y-24 pb-12">
      {/* 1. HERO + PRODUCT PREVIEW */}
      <section className="pt-10 sm:pt-16 pb-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="lg:col-span-6 space-y-6"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="cobalt">NEXORA · The Next Generation Business Developer</Badge>
              <Badge tone="champagne">India-First · Global Ready</Badge>
            </div>

            <h1 className="font-heading text-4xl sm:text-5xl lg:text-[3.35rem] font-extrabold text-[#202B43] leading-[1.08]">
              Your entire business. One intelligent ecosystem.
            </h1>

            <p className="text-base sm:text-lg text-[#4E5D78] leading-relaxed max-w-xl">
              Connect customer relationships, everyday operations and business decisions through one intelligent workspace.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Link to="/early-access">
                <Button variant="primary" size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Explore NEXORA
                </Button>
              </Link>
              <Link to="/platform">
                <Button variant="secondary" size="lg">
                  Discover the platform
                </Button>
              </Link>
            </div>

            <div className="pt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-[#4E5D78]">
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#3867E9]" />
                PostgreSQL Tenant Isolation &amp; RLS
              </span>
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#3867E9]" />
                Transactional Order &amp; Stock Integrity
              </span>
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#22A995]" />
                Human-Approved AI Intelligence
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
            className="lg:col-span-6"
          >
            <EcosystemSyncPreview />
          </motion.div>
        </div>
      </section>

      {/* 2. DISCONNECTED OPERATIONS PROBLEM */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="max-w-2xl mb-10 space-y-3">
          <Badge tone="neutral">The Disconnected Operations Problem</Badge>
          <h2 className="font-heading text-2xl sm:text-4xl font-bold text-[#202B43]">
            Growing SMEs outgrow disconnected spreadsheets and chat threads
          </h2>
          <p className="text-sm sm:text-base text-[#4E5D78]">
            When CRM notes, WhatsApp orders, warehouse counts and daily reporting live in separate tools, teams spend hours reconciling numbers instead of serving customers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            {
              title: 'Scattered customer context',
              desc: 'Follow-ups, commitments and past orders sit across phones, notebooks and email threads.',
              tag: 'CRM Gap',
            },
            {
              title: 'Manual order re-entry',
              desc: 'Clerks copy customer requests by hand into billing tools, slowing fulfilment and inviting errors.',
              tag: 'Order Delay',
            },
            {
              title: 'Inventory mismatches',
              desc: 'Promises are made without real-time stock checks, causing stockouts or negative balances.',
              tag: 'Stock Risk',
            },
            {
              title: 'Delayed management visibility',
              desc: 'Founders wait days for end-of-week spreadsheets instead of acting on live business pulse alerts.',
              tag: 'Blind Spots',
            },
          ].map((item) => (
            <Card key={item.title} accent="sand" className="space-y-3">
              <Badge tone="warning">{item.tag}</Badge>
              <h3 className="font-heading text-lg font-bold text-[#202B43]">{item.title}</h3>
              <p className="text-sm text-[#4E5D78] leading-relaxed">{item.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* 3. NEXORA UNIFIED SOLUTION */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <Card accent="cobalt" className="p-6 sm:p-10 bg-white border-[#E2E8F4] shadow-elevated rounded-3xl">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-6 space-y-4">
              <Badge tone="cobalt">The Unified Architecture</Badge>
              <h2 className="font-heading text-2xl sm:text-4xl font-bold text-[#202B43]">
                One shared PostgreSQL foundation across every team function
              </h2>
              <p className="text-sm sm:text-base text-[#4E5D78] leading-relaxed">
                Every customer profile, lead, order line, inventory adjustment, task and AI insight reads from one tenant-isolated database. When an order confirms, inventory updates inside the same transaction and analytics reflect it immediately.
              </p>
              <div className="pt-2 flex flex-wrap gap-3">
                <Link to="/register">
                  <Button variant="primary" size="md" rightIcon={<ArrowRight className="w-4 h-4" />}>
                    Create Live Workspace
                  </Button>
                </Link>
                <Link to="/platform">
                  <Button variant="secondary" size="md">Inspect Platform Architecture</Button>
                </Link>
              </div>
            </div>

            <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              {[
                {
                  label: 'Relationships',
                  items: 'Customers, Contacts, Leads, Timeline',
                  icon: Users,
                  well: 'bg-[#EAF0FE] text-[#3867E9] border-[#C5D5FA]',
                },
                {
                  label: 'Execution',
                  items: 'Orders, Line Items, Taxes, Fulfilment',
                  icon: ShoppingCart,
                  well: 'bg-[#EAF0FE] text-[#3867E9] border-[#C5D5FA]',
                },
                {
                  label: 'Inventory',
                  items: 'SKUs, Suppliers, Ledger, Reorder Rules',
                  icon: Boxes,
                  well: 'bg-[#FBF4E7] text-[#D69B42] border-[#EBD09F]',
                },
                {
                  label: 'Intelligence',
                  items: 'Business Pulse, Analytics & Gemini Copilot',
                  icon: Database,
                  well: 'bg-[#E6F6F3] text-[#22A995] border-[#99DDD2]',
                },
              ].map((pillar) => {
                const Icon = pillar.icon;
                return (
                  <div key={pillar.label} className="p-4 rounded-2xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-2.5 transition-colors hover:border-[#C5D5FA]">
                    <div className={`w-9 h-9 rounded-xl border flex items-center justify-center ${pillar.well}`}>
                      <Icon className="w-4.5 h-4.5" />
                    </div>
                    <div className="font-heading text-sm font-bold text-[#202B43]">{pillar.label}</div>
                    <div className="text-xs text-[#4E5D78] leading-relaxed">{pillar.items}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      </section>

      {/* 4. SIX PRODUCT CAPABILITIES */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
          <div className="space-y-2 max-w-2xl">
            <Badge tone="forest">Six Core Capabilities</Badge>
            <h2 className="font-heading text-2xl sm:text-4xl font-bold text-[#202B43]">
              Every module built to reinforce the rest of your business
            </h2>
          </div>
          <Link to="/platform" className="text-sm font-semibold text-[#3867E9] hover:underline inline-flex items-center gap-1">
            Explore full platform <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {CAPABILITIES.map((cap) => {
            const Icon = cap.icon;
            const isAi = cap.to === '/ai-automation';
            return (
              <Link key={cap.title} to={cap.to} className="group block">
                <Card interactive accent={isAi ? 'mint' : 'none'} className="h-full flex flex-col justify-between space-y-4">
                  <div className="space-y-3">
                    <div
                      className={`w-11 h-11 rounded-xl flex items-center justify-center transition-colors duration-200 ${
                        isAi
                          ? 'bg-[#E6F6F3] text-[#22A995] group-hover:bg-[#22A995] group-hover:text-white'
                          : 'bg-[#EAF0FE] text-[#3867E9] group-hover:bg-[#3867E9] group-hover:text-white'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <h3 className="font-heading text-lg font-bold text-[#202B43]">{cap.title}</h3>
                    <p className="text-sm text-[#4E5D78] leading-relaxed">{cap.desc}</p>
                  </div>
                  <div className={`text-xs font-bold inline-flex items-center gap-1 pt-2 ${isAi ? 'text-[#127466]' : 'text-[#3867E9]'}`}>
                    <span>Explore module</span>
                    <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      </section>

      {/* 5. HOW NEXORA WORKS */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="max-w-2xl mb-10 space-y-2">
          <Badge tone="cobalt">How NEXORA Works</Badge>
          <h2 className="font-heading text-2xl sm:text-4xl font-bold text-[#202B43]">
            A closed operational loop from inquiry to insight
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {[
            { step: '01', title: 'Capture', body: 'Log new leads, customer inquiries, incoming order messages and contacts cleanly.' },
            { step: '02', title: 'Coordinate', body: 'Assign follow-up tasks, verify stock availability and schedule team handoffs.' },
            { step: '03', title: 'Execute', body: 'Approve orders atomically with row-locked inventory adjustments and audit logs.' },
            { step: '04', title: 'Decide', body: 'Review real-time analytics, Business Pulse priorities and grounded AI briefs.' },
          ].map((item) => (
            <Card key={item.step} accent={item.step === '04' ? 'mint' : 'cobalt'} className="space-y-3">
              <div
                className={`font-mono text-xs font-bold inline-block px-2.5 py-1 rounded-lg ${
                  item.step === '04'
                    ? 'text-[#127466] bg-[#E6F6F3]'
                    : 'text-[#2952C8] bg-[#EAF0FE]'
                }`}
              >
                STEP {item.step}
              </div>
              <h3 className="font-heading text-xl font-bold text-[#202B43]">{item.title}</h3>
              <p className="text-sm text-[#4E5D78] leading-relaxed">{item.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* 6. AI-POWERED BUSINESS INTELLIGENCE + 7. AUTOMATION VISUALIZATION */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card accent="mint" className="lg:col-span-7 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Badge tone="mint">NEXORA Intelligence · Sample Q&amp;A</Badge>
            <Badge tone="champagne">Human-Approval Required</Badge>
          </div>
          <h2 className="font-heading text-2xl font-bold text-[#202B43]">
            Ask plain-language questions grounded strictly in tenant data
          </h2>
          <p className="text-sm text-[#4E5D78]">
            Click a question below to see how NEXORA Intelligence grounds answers in real tables and cites sources rather than fabricating unverified metrics.
          </p>

          <div className="flex flex-wrap gap-2">
            {AI_SAMPLE_PROMPTS.map((item, i) => (
              <button
                key={item.q}
                type="button"
                onClick={() => setSelectedAiIdx(i)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all duration-200 cursor-pointer ${
                  selectedAiIdx === i
                    ? 'bg-[#22A995] text-white border-[#22A995] shadow-sm'
                    : 'bg-[#F6F8FC] text-[#202B43] border-[#E2E8F4] hover:bg-[#E6F6F3]/60 hover:border-[#99DDD2]'
                }`}
              >
                {item.q}
              </button>
            ))}
          </div>

          <div className="p-4 rounded-2xl bg-[#E6F6F3]/65 border border-[#99DDD2] space-y-2">
            <div className="text-xs font-semibold text-[#127466] flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#22A995]" />
              NEXORA Intelligence Response (Illustrative)
            </div>
            <p className="text-sm text-[#202B43] leading-relaxed">{AI_SAMPLE_PROMPTS[selectedAiIdx].a}</p>
            <div className="text-[11px] font-mono text-[#4E5D78] pt-1">
              Grounded Source: {AI_SAMPLE_PROMPTS[selectedAiIdx].source}
            </div>
          </div>
        </Card>

        <Card accent="mint" className="lg:col-span-5 space-y-5">
          <div className="flex items-center justify-between gap-2">
            <Badge tone="mint">Automation Workflow</Badge>
            <Workflow className="w-5 h-5 text-[#22A995]" />
          </div>
          <h2 className="font-heading text-2xl font-bold text-[#202B43]">
            Safeguarded triggers with human checkpoints
          </h2>
          <div className="space-y-3">
            {[
              { tag: 'Trigger', text: 'Stock drops below reorder threshold OR order confirmed' },
              { tag: 'Condition', text: 'Verify tenant permissions & check open draft duplicates' },
              { tag: 'Approval Gate', text: 'Queue draft communication / restock action for review' },
              { tag: 'Execution Log', text: 'Record timestamp, actor, retries & immutable audit entry' },
            ].map((node, idx) => (
              <div key={node.tag} className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex items-start gap-3">
                <span className="w-6 h-6 rounded-lg bg-[#E6F6F3] border border-[#99DDD2] text-[#127466] text-xs font-bold flex items-center justify-center shrink-0">
                  {idx + 1}
                </span>
                <div>
                  <div className="text-xs font-bold text-[#127466] uppercase tracking-wider">{node.tag}</div>
                  <div className="text-xs text-[#4E5D78] mt-0.5">{node.text}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* 8. BUSINESS PULSE PREVIEW */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <Card className="p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <Badge tone="neutral">Business Pulse · Illustrative Sample View</Badge>
              <h2 className="font-heading text-2xl sm:text-3xl font-bold text-[#202B43]">
                One daily operational briefing before your workday starts
              </h2>
            </div>
            <div className="flex gap-2">
              {(
                [
                  { id: 'orders', label: 'Orders Watch' },
                  { id: 'stock', label: 'Low Stock' },
                  { id: 'followups', label: 'Follow-Ups' },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedPulseTab(tab.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border cursor-pointer ${
                    selectedPulseTab === tab.id
                      ? 'bg-[#3867E9] text-white border-[#3867E9]'
                      : 'bg-[#F6F8FC] text-[#4E5D78] border-[#E2E8F4]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#4E5D78]">
                <Clock className="w-4 h-4 text-[#3867E9]" /> Pending Approvals
              </div>
              <div className="font-heading text-2xl font-bold text-[#202B43]">
                {selectedPulseTab === 'orders' ? '3 Draft Orders (Sample)' : selectedPulseTab === 'stock' ? '2 Reorder Requests (Sample)' : '4 Account Calls (Sample)'}
              </div>
              <div className="text-xs text-[#4E5D78]">Inside the authenticated workspace, every count is live SQL.</div>
            </div>
            <div className="p-4 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#8A5B14]">
                <AlertCircle className="w-4 h-4 text-[#D69B42]" /> Exception Alert
              </div>
              <div className="font-heading text-2xl font-bold text-[#202B43]">
                {selectedPulseTab === 'stock' ? '2 Low-Stock SKUs (Sample)' : '1 Delayed Fulfilment (Sample)'}
              </div>
              <div className="text-xs text-[#4E5D78]">Surfaces stalled tasks and threshold breaches automatically.</div>
            </div>
            <div className="p-4 rounded-xl bg-[#E6F6F3]/80 border border-[#99DDD2] space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#127466]">
                <Sparkles className="w-4 h-4 text-[#22A995]" /> AI Suggested Next Action
              </div>
              <div className="text-sm font-bold text-[#202B43]">
                Prepare follow-up summary for team approval
              </div>
              <div className="text-xs text-[#127466]">Zero autonomous external sends without operator confirmation.</div>
            </div>
          </div>
        </Card>
      </section>

      {/* 9. SECURITY + 10. SME USE CASES */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card accent="forest" className="space-y-4">
          <div className="flex items-center justify-between">
            <Badge tone="forest">Security First</Badge>
            <Lock className="w-5 h-5 text-[#3867E9]" />
          </div>
          <h2 className="font-heading text-2xl font-bold text-[#202B43]">
            Engineered around tenant isolation and least privilege
          </h2>
          <ul className="space-y-2.5 text-sm text-[#4E5D78]">
            <li className="flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-[#3867E9] shrink-0 mt-0.5" />
              <span>Argon2id password hashing, HttpOnly session cookies, CSRF tokens &amp; rate-limited authentication.</span>
            </li>
            <li className="flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-[#3867E9] shrink-0 mt-0.5" />
              <span>Tenant ownership verified server-side and defended with PostgreSQL Row-Level Security policies.</span>
            </li>
            <li className="flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-[#3867E9] shrink-0 mt-0.5" />
              <span>Immutable audit logs across logins, role updates, stock movements, orders and AI suggestions.</span>
            </li>
          </ul>
          <Link to="/security" className="inline-flex items-center gap-1 text-sm font-semibold text-[#3867E9] hover:underline">
            Read Security &amp; Privacy Architecture <ArrowRight className="w-4 h-4" />
          </Link>
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <Badge tone="neutral">SME Use Cases</Badge>
            <Building2 className="w-5 h-5 text-[#3867E9]" />
          </div>
          <h2 className="font-heading text-2xl font-bold text-[#202B43]">
            Built for Indian SMEs today, architected for global teams
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {[
              { name: 'Wholesale Distributors', detail: 'Fast dealer reorders, credit/note tracking & warehouse stock locks.' },
              { name: 'Multi-Store Retail', detail: 'Centralized SKU pricing, low-stock reorder alerts & supplier records.' },
              { name: 'Local Operations Teams', detail: 'Assigned dispatch tasks, SLA follow-ups & mobile-ready views.' },
              { name: 'Growing B2B Services', detail: 'Pipeline lead stages, quote/order approvals & executive analytics.' },
            ].map((u) => (
              <div key={u.name} className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4]">
                <div className="font-bold text-[#202B43]">{u.name}</div>
                <div className="text-xs text-[#4E5D78] mt-1">{u.detail}</div>
              </div>
            ))}
          </div>
          <Link to="/solutions/smes" className="inline-flex items-center gap-1 text-sm font-semibold text-[#3867E9] hover:underline">
            Explore SME Workflows <ArrowRight className="w-4 h-4" />
          </Link>
        </Card>
      </section>

      {/* 11. PRODUCT ROADMAP */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <Badge tone="neutral">Product Roadmap</Badge>
            <h2 className="font-heading text-2xl sm:text-3xl font-bold text-[#202B43] mt-2">
              Measured execution from core operations to international scale
            </h2>
          </div>
          <Layers className="w-6 h-6 text-[#3867E9]" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { phase: 'Foundation (Active)', tone: 'cobalt' as const, desc: 'Multi-tenant auth, RBAC, Postgres RLS, CRM, Orders & Atomic Inventory.' },
            { phase: 'Intelligence (Active)', tone: 'mint' as const, desc: 'Business Pulse, grounded Gemini insights, workflow approvals & live analytics.' },
            { phase: 'Connectors (Modular)', tone: 'neutral' as const, desc: 'WhatsApp Business, GST e-invoicing, email sync & payment links via provider adapters.' },
            { phase: 'International Scale', tone: 'champagne' as const, desc: 'Multi-currency rules, regional tax adapters & multi-region Cloud Run deployment.' },
          ].map((r) => (
            <Card key={r.phase} className="space-y-2">
              <Badge tone={r.tone}>{r.phase}</Badge>
              <p className="text-sm text-[#4E5D78] leading-relaxed">{r.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* 12. EARLY ACCESS REGISTRATION */}
      <section id="early-access" className="px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
        <Card accent="champagne" className="p-6 sm:p-10 space-y-6">
          <div className="space-y-2 text-center max-w-xl mx-auto">
            <Badge tone="champagne">Early Access Program</Badge>
            <h2 className="font-heading text-2xl sm:text-3xl font-bold text-[#202B43]">
              Bring NEXORA into your business operations
            </h2>
            <p className="text-sm text-[#4E5D78]">
              Submit your team details below (persisted to PostgreSQL) or{' '}
              <Link to="/register" className="font-semibold text-[#3867E9] underline">
                create a live workspace immediately
              </Link>
              .
            </p>
          </div>

          {earlyDone ? (
            <div className="p-6 rounded-2xl bg-[#E6F6F3] border border-[#99DDD2] text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-[#22A995] mx-auto" />
              <div className="font-heading text-lg font-bold text-[#127466]">Early Access Request Recorded</div>
              <p className="text-sm text-[#4E5D78]">
                Thank you, {earlyForm.full_name}. Want to test the live application right now?{' '}
                <Link to="/login" className="font-semibold text-[#3867E9] underline">Sign in</Link> or{' '}
                <Link to="/register" className="font-semibold text-[#3867E9] underline">register a workspace</Link>.
              </p>
            </div>
          ) : (
            <form onSubmit={submitEarlyAccess} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Full Name"
                required
                placeholder="Claire Bennett"
                value={earlyForm.full_name}
                onChange={(e) => setEarlyForm({ ...earlyForm, full_name: e.target.value })}
              />
              <Input
                label="Work Email"
                type="email"
                required
                placeholder="claire@company.example"
                value={earlyForm.email}
                onChange={(e) => setEarlyForm({ ...earlyForm, email: e.target.value })}
              />
              <Input
                label="Company / Business Name"
                required
                placeholder="Meridian Distributors"
                value={earlyForm.company_name}
                onChange={(e) => setEarlyForm({ ...earlyForm, company_name: e.target.value })}
              />
              <Select
                label="Team Size"
                value={earlyForm.team_size}
                onChange={(e) => setEarlyForm({ ...earlyForm, team_size: e.target.value })}
              >
                <option value="1-5">1 - 5 people</option>
                <option value="6-25">6 - 25 people</option>
                <option value="26-100">26 - 100 people</option>
                <option value="100+">100+ people</option>
              </Select>
              <div className="sm:col-span-2">
                <Textarea
                  label="Primary Workflow Priority"
                  rows={3}
                  placeholder="Tell us what you want connected first: CRM, orders, inventory, GST billing, or analytics..."
                  value={earlyForm.notes}
                  onChange={(e) => setEarlyForm({ ...earlyForm, notes: e.target.value })}
                />
              </div>
              <div className="sm:col-span-2 flex justify-end">
                <Button type="submit" size="lg" loading={earlySubmitting} rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Request Early Access
                </Button>
              </div>
            </form>
          )}
        </Card>
      </section>
    </div>
  );
};
