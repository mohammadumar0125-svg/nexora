import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Target,
  Plus,
  Download,
  Upload,
  ArrowRight,
  Paperclip,
  MessageSquare,
  CheckCircle2,
} from 'lucide-react';
import { Badge, Button, Card, EmptyState, Input, Modal, Select, StatTile, Textarea, useToast } from '../../components/ui';
import { api } from '../../api';
import { Customer, Lead, User } from '../../types';

export const CrmHubPage: React.FC<{ user: User }> = ({ user }) => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);

  useEffect(() => {
    api.listCustomers().then(setCustomers).catch(() => {});
    api.listLeads().then(setLeads).catch(() => {});
  }, []);

  const totalPipeline = leads.filter((l) => l.stage !== 'lost').reduce((sum, l) => sum + Number(l.estimated_value), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="forest">CRM Hub</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            Customer Relationships &amp; Pipeline
          </h1>
        </div>
        <div className="flex gap-2">
          <Link to="/app/customers"><Button variant="secondary" size="sm">Manage Customers</Button></Link>
          <Link to="/app/leads"><Button variant="primary" size="sm">Manage Leads</Button></Link>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatTile label="Total Customers" value={customers.length} icon={<Users className="w-4 h-4" />} accent="forest" />
        <StatTile label="Open Pipeline Leads" value={leads.filter((l) => !['won', 'lost'].includes(l.stage)).length} icon={<Target className="w-4 h-4" />} accent="lime" />
        <StatTile label="Pipeline Value" value={`${user.tenant.currency} ${totalPipeline.toFixed(0)}`} accent="forest" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold">Recent Customer Accounts</h2>
            <Link to="/app/customers" className="text-xs font-semibold text-[#3867E9] underline">View all</Link>
          </div>
          {customers.slice(0, 5).map((c) => (
            <div key={c.id} className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex justify-between items-center text-xs">
              <div>
                <div className="font-bold text-[#202B43]">{c.name}</div>
                <div className="text-[#4E5D78]">{c.category} · {c.phone || 'No phone'}</div>
              </div>
              <Badge tone="forest">{c.status}</Badge>
            </div>
          ))}
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold">Active Leads</h2>
            <Link to="/app/leads" className="text-xs font-semibold text-[#3867E9] underline">View all</Link>
          </div>
          {leads.slice(0, 5).map((l) => (
            <div key={l.id} className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex justify-between items-center text-xs">
              <div>
                <div className="font-bold text-[#202B43]">{l.title}</div>
                <div className="text-[#4E5D78]">{l.company_name}</div>
              </div>
              <Badge tone="lime">{l.stage}</Badge>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
};

export const CustomersPage: React.FC<{ user: User }> = ({ user }) => {
  const { notify } = useToast();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<any | null>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [csvText, setCsvText] = useState('name,category,email,phone,gstin\n');
  const [newForm, setNewForm] = useState({ name: '', category: 'wholesale', email: '', phone: '', gstin: '', billing_address: '' });
  const [noteText, setNoteText] = useState('');
  const [contactForm, setContactForm] = useState({ full_name: '', email: '', phone: '', designation: '' });

  const canWrite = user.permissions.includes('crm:write');

  const load = async (qStr?: string) => {
    setCustomers(await api.listCustomers(qStr));
  };

  useEffect(() => {
    load();
  }, []);

  const openDetail = async (id: string) => {
    const det = await api.getCustomerDetail(id);
    setSelected(det);
    const fls = await api.listFiles('customer', id).catch(() => []);
    setFiles(fls);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCustomer(newForm);
      setCreateOpen(false);
      setNewForm({ name: '', category: 'wholesale', email: '', phone: '', gstin: '', billing_address: '' });
      await load(query);
      notify('Customer account created.', 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Failed to create customer', 'error');
    }
  };

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.importCustomersCsv(csvText);
      setImportOpen(false);
      await load(query);
      notify(`Imported ${res.imported_count} customer record(s).`, 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Import failed', 'error');
    }
  };

  const addActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !noteText.trim()) return;
    await api.logActivity({
      entity_type: 'customer',
      entity_id: selected.customer.id,
      activity_type: 'note',
      summary: noteText,
    });
    setNoteText('');
    await openDetail(selected.customer.id);
    notify('Activity recorded on customer timeline.', 'success');
  };

  const addContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    await api.createContact({ customer_id: selected.customer.id, ...contactForm, is_primary: false });
    setContactForm({ full_name: '', email: '', phone: '', designation: '' });
    await openDetail(selected.customer.id);
    notify('Contact added.', 'success');
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f || !selected) return;
    try {
      await api.uploadFile('customer', selected.customer.id, f);
      setFiles(await api.listFiles('customer', selected.customer.id));
      notify('Attachment encrypted & stored privately.', 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Upload rejected', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="forest">CRM · Customers</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">Customer Directory</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <a href="/api/crm/customers/export/csv">
            <Button variant="secondary" size="sm" leftIcon={<Download className="w-3.5 h-3.5" />}>Export CSV</Button>
          </a>
          {canWrite && (
            <>
              <Button variant="secondary" size="sm" leftIcon={<Upload className="w-3.5 h-3.5" />} onClick={() => setImportOpen(true)}>
                Import CSV
              </Button>
              <Button variant="primary" size="sm" leftIcon={<Plus className="w-3.5 h-3.5" />} onClick={() => setCreateOpen(true)}>
                New Customer
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Search customer name, phone or email..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            load(e.target.value);
          }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 space-y-2.5">
          {!customers.length ? (
            <EmptyState title="No customers found" description="Create or import customers to build your workspace CRM." />
          ) : (
            customers.map((c) => (
              <Card
                key={c.id}
                interactive
                padding="sm"
                onClick={() => openDetail(c.id)}
                className={`cursor-pointer flex items-center justify-between gap-3 ${
                  selected?.customer?.id === c.id ? 'border-[#3867E9] bg-[#EAF0FE]/40' : ''
                }`}
              >
                <div className="min-w-0">
                  <div className="font-heading text-sm font-bold text-[#202B43] truncate">{c.name}</div>
                  <div className="text-xs text-[#4E5D78]">
                    {c.category} · {c.phone || c.email || 'No contact'} · {c.order_count || 0} orders
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="font-mono text-xs font-bold text-[#3867E9]">
                    {user.tenant.currency} {Number(c.total_spent || 0).toFixed(0)}
                  </div>
                  <Badge tone="neutral">{c.status}</Badge>
                </div>
              </Card>
            ))
          )}
        </div>

        <div className="lg:col-span-6">
          {!selected ? (
            <EmptyState
              icon={<Users className="w-5 h-5" />}
              title="Select a customer account"
              description="Inspect contacts, activity timeline, attachments, and past orders on the right."
            />
          ) : (
            <Card accent="forest" className="space-y-5">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <h2 className="font-heading text-xl font-bold text-[#202B43]">{selected.customer.name}</h2>
                  <Badge tone="forest">{selected.customer.category}</Badge>
                </div>
                <div className="text-xs text-[#4E5D78] mt-1 space-y-0.5">
                  <div>{selected.customer.email} · {selected.customer.phone}</div>
                  {selected.customer.gstin && <div className="font-mono">GSTIN: {selected.customer.gstin}</div>}
                  <div>{selected.customer.billing_address}</div>
                </div>
              </div>

              <div className="space-y-2 border-t border-[#E2E8F4] pt-3">
                <div className="text-xs font-bold uppercase tracking-wider text-[#4E5D78]">Contacts</div>
                {selected.contacts.map((ct: any) => (
                  <div key={ct.id} className="p-2.5 rounded-xl bg-[#F6F8FC] text-xs flex justify-between">
                    <span className="font-semibold">{ct.full_name} ({ct.designation || 'Contact'})</span>
                    <span className="text-[#4E5D78]">{ct.phone || ct.email}</span>
                  </div>
                ))}
                {canWrite && (
                  <form onSubmit={addContact} className="grid grid-cols-2 gap-2 pt-1">
                    <Input placeholder="Contact name" required value={contactForm.full_name} onChange={(e) => setContactForm({ ...contactForm, full_name: e.target.value })} />
                    <Input placeholder="Phone" value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })} />
                    <Button type="submit" size="sm" variant="secondary" className="col-span-2">Add Contact</Button>
                  </form>
                )}
              </div>

              <div className="space-y-2 border-t border-[#E2E8F4] pt-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#4E5D78]">Private Attachments</span>
                  {canWrite && (
                    <label className="text-xs font-semibold text-[#3867E9] cursor-pointer underline inline-flex items-center gap-1">
                      <Paperclip className="w-3.5 h-3.5" /> Attach file
                      <input type="file" className="hidden" onChange={handleUpload} />
                    </label>
                  )}
                </div>
                {files.map((f) => (
                  <div key={f.id} className="p-2 rounded-xl bg-[#F6F8FC] flex justify-between items-center text-xs">
                    <span className="font-mono truncate">{f.original_filename}</span>
                    <a href={`/api/files/${f.id}/download`} className="font-semibold text-[#3867E9] underline">Download</a>
                  </div>
                ))}
              </div>

              <div className="space-y-2 border-t border-[#E2E8F4] pt-3">
                <div className="text-xs font-bold uppercase tracking-wider text-[#4E5D78] flex items-center gap-1">
                  <MessageSquare className="w-3.5 h-3.5" /> Activity Timeline
                </div>
                {canWrite && (
                  <form onSubmit={addActivity} className="flex gap-2">
                    <Input placeholder="Log call, note or follow-up summary..." value={noteText} onChange={(e) => setNoteText(e.target.value)} />
                    <Button type="submit" size="sm">Log</Button>
                  </form>
                )}
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {selected.activities.map((a: any) => (
                    <div key={a.id} className="p-2.5 rounded-xl bg-[#F6F8FC] text-xs">
                      <div className="font-semibold text-[#202B43]">{a.summary}</div>
                      <div className="text-[11px] text-[#4E5D78]">{a.activity_type} · {a.author_name || 'Team'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create Customer Account">
        <form onSubmit={handleCreate} className="space-y-3">
          <Input label="Customer / Business Name" required value={newForm.name} onChange={(e) => setNewForm({ ...newForm, name: e.target.value })} />
          <Select label="Category" value={newForm.category} onChange={(e) => setNewForm({ ...newForm, category: e.target.value })}>
            <option value="wholesale">Wholesale</option>
            <option value="retail">Retail</option>
            <option value="enterprise">Enterprise</option>
            <option value="service">Service</option>
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Email" type="email" value={newForm.email} onChange={(e) => setNewForm({ ...newForm, email: e.target.value })} />
            <Input label="Phone" value={newForm.phone} onChange={(e) => setNewForm({ ...newForm, phone: e.target.value })} />
          </div>
          <Input label="GSTIN (Optional)" value={newForm.gstin} onChange={(e) => setNewForm({ ...newForm, gstin: e.target.value })} />
          <Textarea label="Billing Address" rows={2} value={newForm.billing_address} onChange={(e) => setNewForm({ ...newForm, billing_address: e.target.value })} />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Save Customer</Button>
          </div>
        </form>
      </Modal>

      <Modal open={importOpen} onClose={() => setImportOpen(false)} title="Import Customers CSV">
        <form onSubmit={handleImport} className="space-y-3">
          <Textarea
            label="Paste CSV (columns: name,category,email,phone,gstin,billing_address)"
            rows={6}
            value={csvText}
            onChange={(e) => setCsvText(e.target.value)}
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setImportOpen(false)}>Cancel</Button>
            <Button type="submit">Import Records</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export const LeadsPage: React.FC<{ user: User }> = ({ user }) => {
  const { notify } = useToast();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: '', company_name: '', contact_name: '', phone: '', stage: 'new', estimated_value: '0' });

  const canWrite = user.permissions.includes('crm:write');
  const load = () => api.listLeads().then(setLeads);

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.createLead({ ...form, estimated_value: Number(form.estimated_value) || 0 });
    setOpen(false);
    setForm({ title: '', company_name: '', contact_name: '', phone: '', stage: 'new', estimated_value: '0' });
    await load();
    notify('Lead added to pipeline.', 'success');
  };

  const moveStage = async (lead: Lead, stage: string) => {
    await api.updateLead(lead.id, { ...lead, stage });
    await load();
    notify(`Lead moved to ${stage}.`, 'success');
  };

  const convertLead = async (lead: Lead) => {
    const res = await api.convertLead(lead.id);
    await load();
    notify(`Converted to Customer: ${res.customer_name}`, 'success');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="lime">CRM · Pipeline</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">Lead Management</h1>
        </div>
        {canWrite && (
          <Button variant="primary" size="sm" leftIcon={<Plus className="w-3.5 h-3.5" />} onClick={() => setOpen(true)}>
            Add Lead
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {leads.map((l) => (
          <Card key={l.id} accent={l.stage === 'won' ? 'lime' : 'forest'} className="space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="font-heading text-base font-bold text-[#202B43]">{l.title}</h2>
                <div className="text-xs text-[#4E5D78]">{l.company_name}</div>
              </div>
              <Badge tone={l.stage === 'won' ? 'lime' : l.stage === 'lost' ? 'danger' : 'forest'}>
                {l.stage}
              </Badge>
            </div>
            <div className="text-xs text-[#4E5D78] space-y-0.5">
              <div>Contact: {l.contact_name || 'N/A'} · {l.phone || 'No phone'}</div>
              <div className="font-mono font-bold text-[#3867E9]">
                Est. Value: {user.tenant.currency} {Number(l.estimated_value).toFixed(2)}
              </div>
            </div>
            {canWrite && (
              <div className="pt-2 border-t border-[#E2E8F4] flex flex-wrap gap-2">
                <select
                  aria-label={`Change stage for ${l.title}`}
                  value={l.stage}
                  onChange={(e) => moveStage(l, e.target.value)}
                  className="text-xs px-2.5 py-1.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] font-semibold"
                >
                  {['new', 'contacted', 'qualified', 'proposal', 'won', 'lost'].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                {!l.customer_id && l.stage !== 'lost' && (
                  <Button size="sm" variant="lime" rightIcon={<ArrowRight className="w-3 h-3" />} onClick={() => convertLead(l)}>
                    Convert to Customer
                  </Button>
                )}
                {l.customer_id && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#3867E9]">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Customer Linked
                  </span>
                )}
              </div>
            )}
          </Card>
        ))}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Create Pipeline Lead">
        <form onSubmit={handleCreate} className="space-y-3">
          <Input label="Opportunity / Lead Title" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Input label="Company Name" required value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Contact Name" value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} />
            <Input label="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Stage" value={form.stage} onChange={(e) => setForm({ ...form, stage: e.target.value })}>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
              <option value="qualified">Qualified</option>
              <option value="proposal">Proposal</option>
            </Select>
            <Input label="Estimated Value" type="number" min="0" value={form.estimated_value} onChange={(e) => setForm({ ...form, estimated_value: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit">Save Lead</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
