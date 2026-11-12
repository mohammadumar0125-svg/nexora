import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, Mail, ShieldCheck, ArrowRight, FileText, Scale } from 'lucide-react';
import { Badge, Button, Card, Input, Select, Textarea, useToast } from '../../components/ui';
import { api } from '../../api';

export const PricingPage: React.FC = () => {
  const plans = [
    {
      name: 'Starter',
      badge: 'Core Workspace',
      status: 'Proposed · Under Pilot Validation',
      priceDisplay: '[PROPOSED — PILOT VALIDATION]',
      desc: 'Essential shared CRM, order creation, product catalogue and daily Business Pulse for compact teams.',
      features: [
        'Customer, contact & lead pipeline management',
        'Order creation with tax & discount calculation',
        'SKU inventory tracking & low-stock alerts',
        'Role-based access control & immutable audit logs',
        'Business Pulse overview & core exports',
      ],
    },
    {
      name: 'Growth',
      badge: 'AI & Automation',
      status: 'Proposed · Under Pilot Validation',
      priceDisplay: '[PROPOSED — PILOT VALIDATION]',
      accent: 'forest' as const,
      desc: 'Full operational connectivity with NEXORA Intelligence Q&A, approval-gated automations and supplier workflows.',
      features: [
        'Everything in Starter',
        'NEXORA Intelligence natural-language Q&A & follow-up drafts',
        'Workflow automation builder with execution & retry logs',
        'Multi-role approvals, suppliers & inventory valuation',
        'Date-range comparison analytics & CSV reporting',
      ],
    },
    {
      name: 'Scale',
      badge: 'Advanced Governance',
      status: 'Proposed · Under Pilot Validation',
      priceDisplay: '[PROPOSED — PILOT VALIDATION]',
      desc: 'Extended retention controls, custom integration adapters, dedicated security governance and multi-unit scale.',
      features: [
        'Everything in Growth',
        'Configurable tenant data retention & security policies',
        'Custom messaging, payment & accounting connectors',
        'Dedicated onboarding & workflow engineering',
        'Extended automation quotas & audit exports',
      ],
    },
  ];

  const addons = [
    { name: 'Guided Onboarding & Data Import', desc: 'Hands-on migration of customer lists, SKU tables and opening stock balances.' },
    { name: 'Advanced Integrations', desc: 'Custom connectors for regional accounting, ERP, messaging or payment gateways.' },
    { name: 'Additional AI & Automation Capacity', desc: 'Expanded server-side Gemini workflow runs and scheduled briefing jobs.' },
    { name: 'Enterprise Controls', desc: 'Custom retention governance, security review support and dedicated deployment options.' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-16">
      <div className="max-w-3xl space-y-4">
        <Badge tone="champagne">Proposed Commercial Structure · Under Pilot Validation</Badge>
        <h1 className="font-heading text-3xl sm:text-5xl font-extrabold text-[#202B43]">
          Simple tier structure calibrated with pilot businesses
        </h1>
        <p className="text-base sm:text-lg text-[#4E5D78] leading-relaxed">
          All commercial figures remain under pilot validation with Indian SME partners before finalizing public pricing tables. Early access workspaces test full functionality cleanly before commercial billing begins.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {plans.map((p) => (
          <Card key={p.name} accent={p.accent ? 'cobalt' : p.name === 'Scale' ? 'champagne' : 'none'} className="flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <Badge tone={p.name === 'Growth' ? 'mint' : p.name === 'Scale' ? 'champagne' : 'cobalt'}>
                  {p.badge}
                </Badge>
                <span className="text-[11px] font-semibold text-[#8A5B14] bg-[#FBF4E7] border border-[#EBD09F] px-2.5 py-0.5 rounded-full">
                  {p.status}
                </span>
              </div>
              <div>
                <h2 className="font-heading text-2xl font-bold text-[#202B43]">{p.name}</h2>
                <div className="font-mono text-sm font-bold text-[#3867E9] mt-2 px-3 py-2 rounded-xl bg-[#EEF2FA] border border-[#E2E8F4]">
                  {p.priceDisplay}
                </div>
              </div>
              <p className="text-sm text-[#4E5D78] leading-relaxed">{p.desc}</p>
              <ul className="space-y-2.5 pt-2">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-[#202B43]">
                    <CheckCircle2 className="w-4 h-4 text-[#3867E9] shrink-0 mt-0.5" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
            <Link to="/early-access">
              <Button variant={p.accent ? 'primary' : 'secondary'} className="w-full" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Join Pilot Validation
              </Button>
            </Link>
          </Card>
        ))}
      </div>

      <div className="space-y-6">
        <div>
          <Badge tone="neutral">Optional Services &amp; Extensions</Badge>
          <h2 className="font-heading text-2xl font-bold text-[#202B43] mt-2">
            Modular capabilities available alongside any workspace tier
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {addons.map((a) => (
            <Card key={a.name} className="space-y-2">
              <h3 className="font-heading text-base font-bold text-[#202B43]">{a.name}</h3>
              <p className="text-xs text-[#4E5D78] leading-relaxed">{a.desc}</p>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export const ContactPage: React.FC = () => {
  const { notify } = useToast();
  const [form, setForm] = useState({ name: '', email: '', company: '', topic: 'Product Walkthrough', message: '' });
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.submitContact(form);
      setSent(true);
      notify('Message received and recorded cleanly.', 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Unable to send message.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 grid grid-cols-1 lg:grid-cols-12 gap-8">
      <div className="lg:col-span-5 space-y-5">
        <Badge tone="forest">Contact NEXORA</Badge>
        <h1 className="font-heading text-3xl sm:text-4xl font-extrabold text-[#202B43]">
          Speak with the engineering &amp; product team
        </h1>
        <p className="text-sm sm:text-base text-[#4E5D78] leading-relaxed">
          Reach out for pilot onboarding, security architecture questions, enterprise deployment planning or partnership inquiries.
        </p>
        <Card className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-[#3867E9]">
            <Mail className="w-4 h-4" />
            <span>Direct Engineering &amp; Security Contacts</span>
          </div>
          <div className="text-xs text-[#4E5D78] space-y-1 font-mono">
            <div>General: contact@nexora-workspace.local</div>
            <div>Security: security@nexora-workspace.local</div>
            <div>Region: India First · Cloud-Portable</div>
          </div>
        </Card>
      </div>

      <Card accent="forest" className="lg:col-span-7">
        {sent ? (
          <div className="py-10 text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-[#3867E9] mx-auto" />
            <h2 className="font-heading text-xl font-bold text-[#202B43]">Inquiry Saved</h2>
            <p className="text-sm text-[#4E5D78]">Your message has been persisted securely in our operational database.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Your Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <Input label="Work Email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
              <Select label="Topic" value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })}>
                <option value="Product Walkthrough">Product Walkthrough</option>
                <option value="Security & Architecture">Security &amp; Architecture</option>
                <option value="Pilot Onboarding">Pilot Onboarding</option>
                <option value="Other">Other</option>
              </Select>
            </div>
            <Textarea label="Message" required rows={4} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
            <Button type="submit" loading={loading} rightIcon={<ArrowRight className="w-4 h-4" />}>
              Send Inquiry
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
};

export const EarlyAccessPage: React.FC = () => {
  const { notify } = useToast();
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    company_name: '',
    business_type: 'Wholesale & Distribution',
    team_size: '6-25',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.submitEarlyAccess(form);
      setDone(true);
      notify('Early access request saved.', 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Unable to save request.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-6">
      <Badge tone="champagne">Early Access Program</Badge>
      <h1 className="font-heading text-3xl sm:text-4xl font-extrabold text-[#202B43]">
        Join the NEXORA early access cohort
      </h1>
      <p className="text-base text-[#4E5D78]">
        Submit your details to schedule guided workspace onboarding, or <Link to="/register" className="font-semibold text-[#3867E9] underline">create a live multi-tenant workspace</Link> right away.
      </p>
      <Card accent="champagne">
        {done ? (
          <div className="py-8 text-center space-y-3">
            <CheckCircle2 className="w-9 h-9 text-[#3867E9] mx-auto" />
            <h2 className="font-heading text-xl font-bold text-[#202B43]">Registration Recorded</h2>
            <p className="text-sm text-[#4E5D78]">Your organization request for <strong>{form.company_name}</strong> is saved in PostgreSQL.</p>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Full Name" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <Input label="Work Email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <Input label="Business Name" required value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} />
            <Select label="Business Category" value={form.business_type} onChange={(e) => setForm({ ...form, business_type: e.target.value })}>
              <option value="Wholesale & Distribution">Wholesale &amp; Distribution</option>
              <option value="Retail">Retail Operations</option>
              <option value="Manufacturing">Light Manufacturing</option>
              <option value="B2B Services">B2B Services</option>
            </Select>
            <Select label="Team Size" value={form.team_size} onChange={(e) => setForm({ ...form, team_size: e.target.value })}>
              <option value="1-5">1 - 5</option>
              <option value="6-25">6 - 25</option>
              <option value="26-100">26 - 100</option>
              <option value="100+">100+</option>
            </Select>
            <div className="sm:col-span-2">
              <Textarea label="Operational Priorities" rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <div className="sm:col-span-2 flex justify-end">
              <Button type="submit" size="lg" loading={loading}>Submit Early Access Application</Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
};

export const PrivacyPolicyPage: React.FC = () => (
  <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-6">
    <div className="flex items-center gap-2">
      <ShieldCheck className="w-5 h-5 text-[#3867E9]" />
      <Badge tone="forest">Privacy Policy</Badge>
    </div>
    <h1 className="font-heading text-3xl sm:text-4xl font-extrabold text-[#202B43]">
      Data Protection &amp; Privacy Commitment
    </h1>
    <Card className="space-y-4 text-sm text-[#4E5D78] leading-relaxed">
      <p>
        <strong className="text-[#202B43]">1. Purpose &amp; Data Minimization:</strong> NEXORA collects only operational information strictly required to provide workspace authentication, CRM management, order processing, inventory control, analytics and explicit user-initiated AI intelligence queries.
      </p>
      <p>
        <strong className="text-[#202B43]">2. Tenant Ownership &amp; Isolation:</strong> Every tenant owns its business records. Tenant data is logically segregated at both application and PostgreSQL Row-Level Security boundaries and is never used to train public third-party foundation models or exposed to other tenants.
      </p>
      <p>
        <strong className="text-[#202B43]">3. AI Processing Disclosure:</strong> When NEXORA Intelligence sends a user-approved request to configured AI providers (such as Google Gemini), only the minimum required authorized tenant context is supplied, prompt-injection sanitization is applied, and consequential interactions are logged in `ai_interactions`.
      </p>
      <p>
        <strong className="text-[#202B43]">4. Access, Export &amp; Retention:</strong> Workspace owners may configure data retention intervals inside Settings, export portable tenant datasets, or request controlled account erasure. Applicable Digital Personal Data Protection (DPDP) Act compliance processes are structured for formal legal review prior to commercial public launch.
      </p>
    </Card>
  </div>
);

export const TermsOfServicePage: React.FC = () => (
  <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-6">
    <div className="flex items-center gap-2">
      <Scale className="w-5 h-5 text-[#3867E9]" />
      <Badge tone="neutral">Legal</Badge>
    </div>
    <h1 className="font-heading text-3xl sm:text-4xl font-extrabold text-[#202B43]">Terms of Service</h1>
    <Card className="space-y-4 text-sm text-[#4E5D78] leading-relaxed">
      <div className="flex items-center gap-2 text-[#3867E9] font-semibold">
        <FileText className="w-4 h-4" />
        <span>Service Scope &amp; Workspace Governance</span>
      </div>
      <p>
        <strong className="text-[#202B43]">1. Authorized Workspace Use:</strong> Businesses registering a workspace in NEXORA remain responsible for managing user roles, onboarding legitimate staff members and revoking access cleanly when personnel change.
      </p>
      <p>
        <strong className="text-[#202B43]">2. Human-in-Control Operations:</strong> AI-generated drafts, analytics briefs and automation suggestions are advisory operational aids. Operators are responsible for reviewing and confirming sensitive orders, inventory changes and customer communications before execution.
      </p>
      <p>
        <strong className="text-[#202B43]">3. Early Access &amp; Commercial Validation:</strong> Pricing tiers displayed during pilot evaluation are provisional until confirmed in signed commercial agreements.
      </p>
    </Card>
  </div>
);
