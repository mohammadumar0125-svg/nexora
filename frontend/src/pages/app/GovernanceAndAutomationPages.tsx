import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  KeyRound,
  Plug,
  RefreshCw,
  Settings,
  Shield,
  ShieldCheck,
  Workflow,
  Zap,
} from 'lucide-react';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Modal,
  Select,
  useToast,
} from '../../components/ui';
import { api } from '../../api';
import { User } from '../../types';

export const AutomationPage: React.FC<{ user: User }> = ({ user }) => {
  const toast = useToast();
  const [data, setData] = useState<{ workflows: any[]; executions: any[] }>({ workflows: [], executions: [] });
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    description: '',
    trigger_event: 'stock_low',
    action_type: 'create_task',
    requires_approval: true,
  });

  const canWrite = user.permissions.includes('automation:write');

  const refresh = () => {
    api.getAutomations().then(setData).catch(() => {});
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createAutomation(form);
      toast.notify('Automation workflow rule created.', 'success');
      setCreateOpen(false);
      setForm({ name: '', description: '', trigger_event: 'stock_low', action_type: 'create_task', requires_approval: true });
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Could not create workflow', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="mint">Workflow Automation</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            Event Triggers &amp; Approval Queue
          </h1>
        </div>
        {canWrite && (
          <Button variant="primary" size="sm" onClick={() => setCreateOpen(true)}>
            <Zap className="w-4 h-4 mr-1.5" /> Create Rule
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card accent="mint" className="lg:col-span-6 space-y-3">
          <h2 className="font-heading text-base font-bold flex items-center gap-2">
            <Workflow className="w-4 h-4 text-[#22A995]" /> Configured Workflows
          </h2>
          {data.workflows.length === 0 ? (
            <EmptyState icon={<Workflow className="w-6 h-6 text-[#22A995]" />} title="No rules configured" description="Automate task creation or notifications when orders confirm or stock drops." />
          ) : (
            data.workflows.map((w) => (
              <div key={w.id} className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-[#202B43]">{w.name}</span>
                    <Badge tone={w.is_active ? 'mint' : 'neutral'}>{w.is_active ? 'Active' : 'Paused'}</Badge>
                  </div>
                  <p className="text-xs text-[#4E5D78]">{w.description}</p>
                  <div className="text-[11px] font-mono text-[#127466]">
                    WHEN {w.trigger_event} → {w.action_type} {w.requires_approval ? '(Requires Approval)' : '(Auto)'}
                  </div>
                </div>
                {canWrite && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={async () => {
                      await api.toggleAutomation(w.id);
                      refresh();
                    }}
                  >
                    {w.is_active ? 'Pause' : 'Enable'}
                  </Button>
                )}
              </div>
            ))
          )}
        </Card>

        <Card className="lg:col-span-6 space-y-3">
          <h2 className="font-heading text-base font-bold">Execution &amp; Human Approval Queue</h2>
          {data.executions.length === 0 ? (
            <p className="text-xs text-[#4E5D78] py-8">No workflow executions triggered yet.</p>
          ) : (
            data.executions.map((ex) => (
              <div key={ex.id} className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#202B43]">{ex.workflow_name}</span>
                  <Badge tone={ex.status === 'executed' ? 'lime' : ex.status === 'pending_approval' ? 'warning' : 'danger'}>
                    {ex.status.replace('_', ' ')}
                  </Badge>
                </div>
                {ex.result_summary && <p className="text-[#4E5D78]">{ex.result_summary}</p>}
                {ex.error_message && <p className="text-red-700">{ex.error_message}</p>}
                {canWrite && (
                  <div className="flex gap-2">
                    {ex.status === 'pending_approval' && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={async () => {
                          await api.approveExecution(ex.id);
                          toast.notify('Workflow execution approved and run.', 'success');
                          refresh();
                        }}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approve &amp; Run
                      </Button>
                    )}
                    {ex.status === 'failed' && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={async () => {
                          await api.retryExecution(ex.id);
                          toast.notify('Execution retried.', 'info');
                          refresh();
                        }}
                      >
                        <RefreshCw className="w-3.5 h-3.5 mr-1" /> Retry
                      </Button>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </Card>
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create Automation Workflow">
        <form onSubmit={handleCreate} className="space-y-3">
          <Input label="Workflow Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Select label="Trigger Event" value={form.trigger_event} onChange={(e) => setForm({ ...form, trigger_event: e.target.value })}>
            <option value="stock_low">Stock falls at/below reorder point</option>
            <option value="order_confirmed">Sales order confirmed</option>
            <option value="lead_won">Lead converted / won</option>
            <option value="followup_overdue">Lead follow-up overdue</option>
          </Select>
          <Select label="Action Type" value={form.action_type} onChange={(e) => setForm({ ...form, action_type: e.target.value })}>
            <option value="create_task">Create Team Follow-Up Task</option>
            <option value="queue_notification">Send Workspace Notification</option>
            <option value="draft_followup">Generate AI Follow-Up Draft</option>
          </Select>
          <label className="flex items-center gap-2 text-xs font-medium text-[#202B43]">
            <input
              type="checkbox"
              checked={form.requires_approval}
              onChange={(e) => setForm({ ...form, requires_approval: e.target.checked })}
            />
            Require human approval before executing action
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Save Workflow</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export const IntegrationsPage: React.FC<{ user: User }> = ({ user }) => {
  const toast = useToast();
  const [items, setItems] = useState<any[]>([]);
  const canEdit = user.permissions.includes('settings:write');

  const refresh = () => {
    api.listIntegrations().then(setItems).catch(() => {});
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleToggleStatus = async (item: any) => {
    const nextStatus = item.status === 'configured' ? 'not_configured' : 'configured';
    try {
      await api.updateIntegration(item.provider_key, { status: nextStatus, notes: item.notes || '' });
      toast.notify(`${item.display_name} status updated to ${nextStatus}.`, 'success');
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Update failed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <Badge tone="forest">Ecosystem Connectors</Badge>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
          Integrations &amp; Honest Adapter Status
        </h1>
        <p className="text-sm text-[#4E5D78] mt-1">
          External services operate behind pluggable adapters and are explicitly reported as configured or not configured.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((it) => (
          <Card key={it.provider_key} className="space-y-3 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="w-9 h-9 rounded-xl bg-[#F3F6FE] text-[#3867E9] flex items-center justify-center">
                  <Plug className="w-4 h-4" />
                </div>
                <Badge tone={it.status === 'configured' ? 'lime' : 'neutral'}>{it.status.replace('_', ' ')}</Badge>
              </div>
              <h2 className="font-heading text-base font-bold text-[#202B43]">{it.display_name}</h2>
              <p className="text-xs text-[#4E5D78]">{it.description}</p>
              {it.notes && <p className="text-[11px] font-mono text-[#3867E9]">Note: {it.notes}</p>}
            </div>
            {canEdit && (
              <Button size="sm" variant="secondary" onClick={() => handleToggleStatus(it)}>
                Toggle Adapter Flag
              </Button>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};

export const SettingsPage: React.FC<{ user: User; onRefreshUser: () => void }> = ({ user, onRefreshUser }) => {
  const toast = useToast();
  const [form, setForm] = useState({ name: '', currency: 'INR', timezone: 'Asia/Kolkata', retention_days: '365', tax_id: '' });
  const canEdit = user.permissions.includes('settings:write');

  useEffect(() => {
    api.getSettings().then((s) => {
      setForm({
        name: s.name || '',
        currency: s.currency || 'INR',
        timezone: s.timezone || 'Asia/Kolkata',
        retention_days: String(s.retention_days || 365),
        tax_id: s.tax_id || '',
      });
    }).catch(() => {});
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.updateSettings({
        ...form,
        retention_days: Number(form.retention_days),
      });
      toast.notify('Workspace settings updated.', 'success');
      onRefreshUser();
    } catch (err: any) {
      toast.notify(err.message || 'Could not update settings', 'error');
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <Badge tone="forest">Workspace Settings</Badge>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
          Organization Profile &amp; Data Retention
        </h1>
      </div>

      <Card>
        <form onSubmit={handleSave} className="space-y-4">
          <Input label="Workspace Name" disabled={!canEdit} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Select label="Currency" disabled={!canEdit} value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })}>
              <option value="INR">INR (Indian Rupee)</option>
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
              <option value="GBP">GBP (British Pound)</option>
            </Select>
            <Input label="Timezone" disabled={!canEdit} value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input label="Retention Policy (Days)" type="number" disabled={!canEdit} value={form.retention_days} onChange={(e) => setForm({ ...form, retention_days: e.target.value })} />
            <Input label="GSTIN / Tax Registration ID" disabled={!canEdit} value={form.tax_id} onChange={(e) => setForm({ ...form, tax_id: e.target.value })} />
          </div>
          {canEdit ? (
            <Button type="submit" variant="primary" leftIcon={<Settings className="w-4 h-4 shrink-0" />}>
              Save Workspace Settings
            </Button>
          ) : (
            <p className="text-xs text-[#4E5D78]">Read-only view. Only Owner or Admin can edit settings.</p>
          )}
        </form>
      </Card>
    </div>
  );
};

export const SecurityPage: React.FC<{ user: User; onRefreshUser: () => void }> = ({ user, onRefreshUser }) => {
  const toast = useToast();
  const [sessions, setSessions] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [mfaSetup, setMfaSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [totpCode, setTotpCode] = useState('');
  const [pwdForm, setPwdForm] = useState({ current_password: '', new_password: '' });

  const canAudit = user.permissions.includes('security:read');

  const refresh = () => {
    api.listSessions().then(setSessions).catch(() => {});
    if (canAudit) {
      api.getAuditLogs().then(setAuditLogs).catch(() => {});
    }
  };

  useEffect(() => {
    refresh();
  }, [canAudit]);

  const handleStartMfa = async () => {
    try {
      const setup = await api.setupMfa();
      setMfaSetup(setup);
    } catch (err: any) {
      toast.notify(err.message || 'MFA setup failed', 'error');
    }
  };

  const handleConfirmMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaSetup) return;
    try {
      await api.confirmMfa(mfaSetup.secret, totpCode);
      toast.notify('TOTP Multi-Factor Authentication activated.', 'success');
      setMfaSetup(null);
      setTotpCode('');
      onRefreshUser();
    } catch (err: any) {
      toast.notify(err.message || 'Invalid TOTP verification code', 'error');
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.changePassword(pwdForm.current_password, pwdForm.new_password);
      toast.notify('Password rotated and other sessions revoked.', 'success');
      setPwdForm({ current_password: '', new_password: '' });
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Password change failed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <Badge tone="forest">Security &amp; Audit</Badge>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
          Account MFA, Sessions &amp; Immutable Audit Trail
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#3867E9]" /> Multi-Factor Authentication (TOTP)
            </h2>
            <Badge tone={user.mfa_enabled ? 'lime' : 'neutral'}>
              {user.mfa_enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>
          {!user.mfa_enabled ? (
            !mfaSetup ? (
              <div className="space-y-3">
                <p className="text-xs text-[#4E5D78]">
                  Protect your account with RFC 6238 authenticator app verification on sign-in.
                </p>
                <Button size="sm" variant="primary" onClick={handleStartMfa}>Setup Authenticator MFA</Button>
              </div>
            ) : (
              <form onSubmit={handleConfirmMfa} className="space-y-3">
                <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] text-xs space-y-1">
                  <div className="font-bold text-[#3867E9]">Secret Key (enter in Google/Microsoft Authenticator):</div>
                  <code className="font-mono text-sm font-bold block">{mfaSetup.secret}</code>
                  <div className="text-[11px] text-[#4E5D78] break-all">URI: {mfaSetup.otpauth_uri}</div>
                </div>
                <Input label="Enter 6-Digit Code" required value={totpCode} onChange={(e) => setTotpCode(e.target.value)} />
                <div className="flex gap-2">
                  <Button type="button" size="sm" variant="secondary" onClick={() => setMfaSetup(null)}>Cancel</Button>
                  <Button type="submit" size="sm" variant="primary">Verify &amp; Enable MFA</Button>
                </div>
              </form>
            )
          ) : (
            <Button
              size="sm"
              variant="danger"
              onClick={async () => {
                await api.disableMfa();
                toast.notify('MFA disabled on account.', 'info');
                onRefreshUser();
              }}
            >
              Disable MFA
            </Button>
          )}
        </Card>

        <Card className="space-y-4">
          <h2 className="font-heading text-base font-bold flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-[#3867E9]" /> Rotate Password
          </h2>
          <form onSubmit={handlePasswordChange} className="space-y-3">
            <Input
              label="Current Password"
              type="password"
              required
              value={pwdForm.current_password}
              onChange={(e) => setPwdForm({ ...pwdForm, current_password: e.target.value })}
            />
            <Input
              label="New Password (10+ chars, upper/lower/digit/symbol)"
              type="password"
              required
              value={pwdForm.new_password}
              onChange={(e) => setPwdForm({ ...pwdForm, new_password: e.target.value })}
            />
            <Button type="submit" size="sm" variant="primary">Update Password</Button>
          </form>
        </Card>
      </div>

      <Card className="space-y-3">
        <h2 className="font-heading text-base font-bold">Active Authenticated Sessions</h2>
        <div className="space-y-2">
          {sessions.map((s) => (
            <div key={s.id} className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex flex-wrap items-center justify-between gap-2 text-xs">
              <div>
                <div className="font-semibold text-[#202B43]">
                  {s.user_agent || 'Web Client'} {s.is_current && <Badge tone="lime">Current Session</Badge>}
                </div>
                <div className="text-[#4E5D78]">IP: {s.ip_address} · Last active: {String(s.last_seen_at).slice(0, 19)}</div>
              </div>
              {!s.is_current && (
                <Button
                  size="sm"
                  variant="danger"
                  onClick={async () => {
                    await api.revokeSession(s.id);
                    toast.notify('Session revoked.', 'info');
                    refresh();
                  }}
                >
                  Revoke
                </Button>
              )}
            </div>
          ))}
        </div>
      </Card>

      {canAudit && (
        <Card className="overflow-x-auto p-0">
          <div className="p-4 border-b border-[#E2E8F4] font-heading text-sm font-bold flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#3867E9]" /> Append-Only Tenant Audit Trail ({auditLogs.length})
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-[#F6F8FC] border-b border-[#E2E8F4] text-[#4E5D78]">
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Actor</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Entity</th>
                <th className="py-2.5 px-3">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F4]">
              {auditLogs.map((al) => (
                <tr key={al.id}>
                  <td className="py-2 px-3 font-mono text-[11px]">{String(al.created_at).slice(0, 19)}</td>
                  <td className="py-2 px-3">{al.actor_name || al.actor_email || 'System'}</td>
                  <td className="py-2 px-3 font-semibold text-[#3867E9]">{al.action}</td>
                  <td className="py-2 px-3 font-mono text-[11px]">{al.entity_type} {al.entity_id ? `(${al.entity_id.slice(0, 8)})` : ''}</td>
                  <td className="py-2 px-3 font-mono text-[11px]">{al.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
};
