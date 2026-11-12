import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  Bell,
  CheckCheck,
  CheckSquare,
  Download,
  FileSpreadsheet,
  Info,
  Plus,
  UserPlus,
  Users,
} from 'lucide-react';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Modal,
  Select,
  StatTile,
  Textarea,
  useToast,
} from '../../components/ui';
import { api } from '../../api';
import { NotificationItem, TaskItem, User } from '../../types';

export const AnalyticsPage: React.FC<{ user: User }> = ({ user }) => {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<any | null>(null);

  useEffect(() => {
    api.getAnalytics(days).then(setData).catch(() => {});
  }, [days]);

  if (!data) {
    return <Card>Loading verified PostgreSQL analytics...</Card>;
  }

  const maxDailyRev = Math.max(1, ...(data.daily_series || []).map((d: any) => Number(d.revenue) || 0));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Badge tone="forest">Business Analytics</Badge>
            {data.is_sample_workspace && <Badge tone="warning">Sample Demo Data</Badge>}
          </div>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            Workspace Performance &amp; Valuation
          </h1>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                days === d
                  ? 'bg-[#3867E9] text-white border-[#3867E9]'
                  : 'bg-white text-[#4E5D78] border-[#E2E8F4]'
              }`}
            >
              Last {d}d
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatTile
          label={`Revenue (${days}d)`}
          value={`${user.tenant.currency} ${Math.round(Number(data.current_period.revenue)).toLocaleString()}`}
          detail={`Prev period: ${user.tenant.currency} ${Math.round(Number(data.previous_period.revenue)).toLocaleString()}`}
          accent="forest"
        />
        <StatTile
          label={`Orders (${days}d)`}
          value={data.current_period.order_count}
          detail={`${data.current_period.confirmed_orders} stock-confirmed`}
          accent="lime"
        />
        <StatTile
          label="Stock Cost Valuation"
          value={`${user.tenant.currency} ${Math.round(Number(data.inventory.cost_valuation)).toLocaleString()}`}
          detail={`${data.inventory.low_stock_skus} low stock SKU(s)`}
          accent={data.inventory.low_stock_skus > 0 ? 'sand' : 'forest'}
        />
        <StatTile
          label="Customer Accounts"
          value={data.customers.total_customers}
          detail={`+${data.customers.new_customers_period} in last ${days}d`}
          accent="forest"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold text-[#202B43] flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#3867E9]" /> Daily Order Revenue ({days}d)
            </h2>
            <span className="text-xs text-[#4E5D78]">Non-cancelled DB records</span>
          </div>
          {(data.daily_series || []).length === 0 ? (
            <p className="text-xs text-[#4E5D78] py-8">No non-cancelled orders recorded in this window.</p>
          ) : (
            <div className="space-y-2.5">
              {data.daily_series.map((d: any) => {
                const pct = Math.max(6, Math.round((Number(d.revenue) / maxDailyRev) * 100));
                return (
                  <div key={d.day} className="space-y-1.5 text-xs">
                    <div className="flex justify-between">
                      <span className="font-mono text-[#4E5D78]">{d.day} ({d.orders} ord)</span>
                      <span className="font-mono font-bold text-[#202B43]">{user.tenant.currency} {Number(d.revenue).toLocaleString()}</span>
                    </div>
                    <div className="h-2.5 rounded-full bg-[#EEF2FA] overflow-hidden">
                      <div className="h-full bg-[#3867E9] rounded-full transition-all duration-500 ease-out" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        <Card className="lg:col-span-5 space-y-4">
          <h2 className="font-heading text-base font-bold text-[#202B43]">CRM Pipeline Distribution</h2>
          <div className="space-y-2">
            {(data.pipeline_by_stage || []).map((st: any) => (
              <div key={st.stage} className="p-2.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex justify-between items-center text-xs">
                <span className="font-semibold capitalize">{st.stage} ({st.count})</span>
                <span className="font-mono font-bold text-[#3867E9]">{user.tenant.currency} {Number(st.value).toLocaleString()}</span>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-xl bg-[#E6F6F3]/60 border border-[#99DDD2] space-y-1.5 text-xs">
            <div className="font-bold text-[#127466] flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-[#22A995]" /> Calculation Definitions
            </div>
            {Object.entries(data.definitions || {}).map(([k, v]: [string, any]) => (
              <div key={k} className="text-[11px] text-[#4E5D78]">
                <span className="font-semibold text-[#202B43] capitalize">{k.replace('_', ' ')}:</span> {v}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export const TasksPage: React.FC<{ user: User }> = () => {
  const toast = useToast();
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium', due_at: '' });

  const refresh = () => {
    api.listTasks().then(setTasks).catch(() => {});
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createTask({
        ...form,
        due_at: form.due_at ? new Date(form.due_at).toISOString() : null,
      });
      toast.notify('Task added to workspace.', 'success');
      setModalOpen(false);
      setForm({ title: '', description: '', priority: 'medium', due_at: '' });
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Could not create task', 'error');
    }
  };

  const handleStatusChange = async (id: string, status: string) => {
    try {
      await api.updateTask(id, { status });
      toast.notify(`Task marked ${status.replace('_', ' ')}.`, 'success');
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Failed to update task', 'error');
    }
  };

  const visible = tasks.filter((t) => (filter === 'all' ? true : t.status === filter));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="forest">Tasks &amp; Follow-Ups</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            Team Action Queue
          </h1>
        </div>
        <Button variant="primary" size="sm" onClick={() => setModalOpen(true)}>
          <Plus className="w-4 h-4 mr-1" /> New Task
        </Button>
      </div>

      <div className="flex gap-2">
        {['all', 'todo', 'in_progress', 'done'].map((st) => (
          <button
            key={st}
            onClick={() => setFilter(st)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold capitalize border ${
              filter === st ? 'bg-[#3867E9] text-white border-[#3867E9]' : 'bg-white text-[#4E5D78] border-[#E2E8F4]'
            }`}
          >
            {st.replace('_', ' ')}
          </button>
        ))}
      </div>

      <Card className="space-y-3">
        {visible.length === 0 ? (
          <EmptyState icon={<CheckSquare className="w-6 h-6" />} title="No tasks in this view" description="Create a follow-up task or switch filters." />
        ) : (
          visible.map((t) => (
            <div key={t.id} className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`font-semibold text-sm ${t.status === 'done' ? 'line-through text-[#4E5D78]' : 'text-[#202B43]'}`}>
                    {t.title}
                  </span>
                  <Badge tone={t.priority === 'urgent' || t.priority === 'high' ? 'warning' : 'neutral'}>
                    {t.priority}
                  </Badge>
                </div>
                {t.description && <p className="text-xs text-[#4E5D78] mt-1">{t.description}</p>}
                <div className="text-[11px] text-[#4E5D78] mt-1">
                  Assignee: {t.assignee_name || 'Unassigned'} {t.due_at ? `· Due ${t.due_at.slice(0, 10)}` : ''}
                </div>
              </div>
              <select
                value={t.status}
                onChange={(e) => handleStatusChange(t.id, e.target.value)}
                className="rounded-xl border border-[#E2E8F4] bg-white px-3 py-1.5 text-xs font-semibold"
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            </div>
          ))
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Create Task">
        <form onSubmit={handleCreate} className="space-y-3">
          <Input label="Title" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Textarea label="Description" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Select label="Priority" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </Select>
            <Input label="Due Date" type="date" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Create Task</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export const NotificationsPage: React.FC<{ user: User }> = () => {
  const toast = useToast();
  const [items, setItems] = useState<NotificationItem[]>([]);

  const refresh = () => {
    api.listNotifications().then(setItems).catch(() => {});
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleMarkAll = async () => {
    await api.markAllNotificationsRead();
    toast.notify('All alerts marked read.', 'success');
    refresh();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="forest">Notifications Center</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            Operational &amp; Approval Alerts
          </h1>
        </div>
        <Button variant="secondary" size="sm" onClick={handleMarkAll}>
          <CheckCheck className="w-4 h-4 mr-1.5" /> Mark All Read
        </Button>
      </div>

      <Card className="space-y-3">
        {items.length === 0 ? (
          <EmptyState icon={<Bell className="w-6 h-6" />} title="No alerts yet" description="Stock warnings, pending approvals, and workflow alerts appear here." />
        ) : (
          items.map((n) => (
            <div
              key={n.id}
              className={`p-3.5 rounded-xl border flex items-start justify-between gap-3 ${
                n.is_read ? 'bg-white border-[#E2E8F4]' : 'bg-[#F3F6FE] border-[#3867E9]/30'
              }`}
            >
              <div>
                <div className="flex items-center gap-2">
                  <Badge tone={n.is_read ? 'neutral' : 'forest'}>{n.category}</Badge>
                  <span className="font-semibold text-sm text-[#202B43]">{n.title}</span>
                </div>
                <p className="text-xs text-[#4E5D78] mt-1">{n.body}</p>
              </div>
              {!n.is_read && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={async () => {
                    await api.markNotificationRead(n.id);
                    refresh();
                  }}
                >
                  Mark Read
                </Button>
              )}
            </div>
          ))
        )}
      </Card>
    </div>
  );
};

export const TeamPage: React.FC<{ user: User }> = ({ user }) => {
  const toast = useToast();
  const [data, setData] = useState<{ members: any[]; invitations: any[]; roles: any[] }>({
    members: [],
    invitations: [],
    roles: [],
  });
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('staff');
  const [inviteLink, setInviteLink] = useState('');

  const canManage = user.permissions.includes('team:manage');

  const refresh = () => {
    api.getTeam().then(setData).catch(() => {});
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.inviteMember(inviteEmail, inviteRole);
      toast.notify(`Invitation issued for ${res.email}.`, 'success');
      if (res.invite_url || res.invite_token) {
        setInviteLink(
          res.invite_url
            ? `${window.location.origin}${res.invite_url}`
            : `${window.location.origin}/accept-invite?token=${res.invite_token}`
        );
      }
      setInviteEmail('');
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Could not issue invitation', 'error');
    }
  };

  const handleUpdate = async (userId: string, body: { role_code?: string; status?: string }) => {
    try {
      await api.updateMembership(userId, body);
      toast.notify('Membership updated & active sessions synced.', 'success');
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Membership update failed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <Badge tone="forest">Team &amp; RBAC Governance</Badge>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
          Workspace Members, Invitations &amp; Permissions
        </h1>
      </div>

      {canManage && (
        <Card className="space-y-4">
          <h2 className="font-heading text-base font-bold flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-[#3867E9]" /> Invite Teammate
          </h2>
          <form onSubmit={handleInvite} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
            <div className="md:col-span-6">
              <Input
                label="Work Email"
                type="email"
                required
                placeholder="colleague@company.example"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <div className="md:col-span-3">
              <Select label="Role" value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
                <option value="staff">Staff</option>
                <option value="viewer">Viewer</option>
              </Select>
            </div>
            <div className="md:col-span-3">
              <Button type="submit" variant="primary" className="w-full">Generate Invite</Button>
            </div>
          </form>
          {inviteLink && (
            <div className="p-3 rounded-xl bg-[#F3F6FE] border border-[#3867E9]/30 text-xs break-all">
              <span className="font-bold text-[#3867E9]">Development Invite Link (copy to send): </span>
              <code className="font-mono">{inviteLink}</code>
            </div>
          )}
        </Card>
      )}

      <Card className="overflow-x-auto p-0">
        <div className="p-4 border-b border-[#E2E8F4] font-heading text-sm font-bold flex items-center gap-2">
          <Users className="w-4 h-4 text-[#3867E9]" /> Workspace Members ({data.members.length})
        </div>
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-[#F6F8FC] border-b border-[#E2E8F4] text-[#4E5D78]">
              <th className="py-3 px-4">User</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">MFA</th>
              <th className="py-3 px-4">Status</th>
              {canManage && <th className="py-3 px-4 text-right">Controls</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F4]">
            {data.members.map((m) => (
              <tr key={m.membership_id}>
                <td className="py-3 px-4">
                  <div className="font-semibold text-[#202B43]">{m.full_name}</div>
                  <div className="text-[11px] text-[#4E5D78]">{m.email}</div>
                </td>
                <td className="py-3 px-4">
                  {canManage && m.user_id !== user.id ? (
                    <select
                      value={m.role_code}
                      onChange={(e) => handleUpdate(m.user_id, { role_code: e.target.value })}
                      className="rounded-lg border border-[#E2E8F4] px-2 py-1 bg-white text-xs capitalize"
                    >
                      <option value="owner">owner</option>
                      <option value="admin">admin</option>
                      <option value="manager">manager</option>
                      <option value="staff">staff</option>
                      <option value="viewer">viewer</option>
                    </select>
                  ) : (
                    <Badge tone="forest">{m.role_code}</Badge>
                  )}
                </td>
                <td className="py-3 px-4">
                  <Badge tone={m.mfa_enabled ? 'lime' : 'neutral'}>{m.mfa_enabled ? 'Enabled' : 'Off'}</Badge>
                </td>
                <td className="py-3 px-4">
                  <Badge tone={m.status === 'active' ? 'lime' : 'danger'}>{m.status}</Badge>
                </td>
                {canManage && (
                  <td className="py-3 px-4 text-right">
                    {m.user_id !== user.id && (
                      <Button
                        size="sm"
                        variant={m.status === 'active' ? 'danger' : 'secondary'}
                        onClick={() =>
                          handleUpdate(m.user_id, { status: m.status === 'active' ? 'suspended' : 'active' })
                        }
                      >
                        {m.status === 'active' ? 'Suspend' : 'Reactivate'}
                      </Button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card className="space-y-3">
        <h2 className="font-heading text-base font-bold">Role Permission Matrix</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.roles.map((r) => (
            <div key={r.code} className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-1.5 text-xs">
              <div className="font-bold text-[#3867E9] capitalize">{r.name} ({r.code})</div>
              <div className="flex flex-wrap gap-1">
                {(r.permissions || []).map((p: string) => (
                  <span key={p} className="px-1.5 py-0.5 rounded bg-white border border-[#E2E8F4] font-mono text-[10px]">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export const ReportsPage: React.FC<{ user: User }> = ({ user }) => {
  const canSecurity = user.permissions.includes('security:read');

  const reports = [
    {
      key: 'orders',
      title: 'Sales Orders CSV Export',
      desc: 'All non-sensitive order headers, customer names, subtotals, tax breakdowns, and lifecycle statuses scoped cleanly to your tenant.',
      allowed: true,
    },
    {
      key: 'inventory',
      title: 'Inventory Valuation CSV Export',
      desc: 'Current quantity on hand, reorder thresholds, unit prices, and SKU cost prices across warehouse items.',
      allowed: true,
    },
    {
      key: 'audit',
      title: 'Security Audit Log CSV Export',
      desc: 'Immutable ledger of authentication events, order approvals, role updates, and AI interactions (requires security:read).',
      allowed: canSecurity,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <Badge tone="forest">Exports &amp; Compliance Reports</Badge>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
          Tenant-Scoped CSV Reports
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {reports.map((r) => (
          <Card key={r.key} className="flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-[#F3F6FE] text-[#3867E9] flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <h2 className="font-heading text-base font-bold text-[#202B43]">{r.title}</h2>
              <p className="text-xs text-[#4E5D78] leading-relaxed">{r.desc}</p>
            </div>
            {r.allowed ? (
              <a
                href={`/api/reports/export?report_type=${r.key}`}
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-[#3867E9] text-white text-xs font-semibold hover:bg-[#2952C8]"
              >
                <Download className="w-4 h-4" /> Download CSV
              </a>
            ) : (
              <Badge tone="neutral">Requires security:read permission</Badge>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};
