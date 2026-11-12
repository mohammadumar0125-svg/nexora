import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Clock,
  AlertTriangle,
  Boxes,
  Users,
  CheckSquare,
  Sparkles,
  CheckCircle2,
  XCircle,
  Send,
  RefreshCw,
} from 'lucide-react';
import { Badge, Button, Card, EmptyState, StatTile, Textarea, useToast } from '../../components/ui';
import { api } from '../../api';
import { AiInteraction, User } from '../../types';

const EXAMPLE_QUESTIONS = [
  'Which orders are delayed?',
  'Which customers need follow-up?',
  'Which products have low stock?',
  'What tasks require attention today?',
  "Summarise this week's business activity.",
];

export const OverviewPulsePage: React.FC<{ user: User }> = ({ user }) => {
  const [pulse, setPulse] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const loadPulse = async () => {
    setLoading(true);
    try {
      setPulse(await api.getPulse());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPulse();
  }, []);

  if (loading) {
    return <div className="p-8 text-sm text-[#4E5D78]">Loading live Business Pulse from PostgreSQL...</div>;
  }

  const s = pulse?.summary || {};

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Badge tone="cobalt">Business Pulse</Badge>
            {user.tenant.is_sample && <Badge tone="champagne">Sample Evaluation Data</Badge>}
          </div>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1.5">
            Daily Operational Overview
          </h1>
          <p className="text-sm text-[#4E5D78]">
            Every figure below is queried directly from authorized PostgreSQL records in <strong>{user.tenant.name}</strong>.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={loadPulse} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
          Refresh Pulse
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatTile label="Pending Orders" value={s.pending_orders_count ?? 0} accent="cobalt" icon={<Clock className="w-4 h-4" />} detail="Awaiting approval or confirmation" />
        <StatTile label="Delayed Orders" value={s.delayed_orders_count ?? 0} accent="champagne" icon={<AlertTriangle className="w-4 h-4" />} detail="Past target due window" />
        <StatTile label="Low Stock SKUs" value={s.low_stock_count ?? 0} accent="champagne" icon={<Boxes className="w-4 h-4" />} detail="At or below reorder threshold" />
        <StatTile label="Open Follow-Ups" value={s.followups_count ?? 0} accent="mint" icon={<Users className="w-4 h-4" />} detail="Active CRM pipeline leads" />
        <StatTile label="Open Tasks" value={s.open_tasks_count ?? 0} accent="cobalt" icon={<CheckSquare className="w-4 h-4" />} detail="Pending team execution" />
      </div>

      <Card accent="mint" className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#22A995]" />
            <h2 className="font-heading text-base font-bold text-[#202B43]">Operational Priorities &amp; Suggested Actions</h2>
          </div>
          <Link to="/app/intelligence">
            <Button variant="mint" size="sm">Open AI Intelligence</Button>
          </Link>
        </div>
        <ul className="space-y-2 text-sm text-[#202B43]">
          {(pulse?.recommendations || []).map((rec: string) => (
            <li key={rec} className="flex items-start gap-2 p-2.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4]">
              <CheckCircle2 className="w-4 h-4 text-[#22A995] shrink-0 mt-0.5" />
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold text-[#202B43]">Pending &amp; Delayed Orders</h2>
            <Link to="/app/orders" className="text-xs font-semibold text-[#3867E9] underline">Manage Orders</Link>
          </div>
          {!pulse?.pending_orders?.length && !pulse?.delayed_orders?.length ? (
            <EmptyState title="No pending orders" description="All created orders have been confirmed or closed." />
          ) : (
            <div className="space-y-2">
              {pulse.pending_orders.map((o: any) => (
                <div key={o.id} className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex items-center justify-between text-xs">
                  <div>
                    <span className="font-mono font-bold text-[#3867E9]">{o.order_number}</span>
                    <span className="ml-2 font-semibold">{o.customer_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold">{user.tenant.currency} {Number(o.total_amount).toFixed(2)}</span>
                    <Badge tone="warning">{o.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold text-[#202B43]">Low-Stock Alerts</h2>
            <Link to="/app/inventory" className="text-xs font-semibold text-[#3867E9] underline">Open Inventory</Link>
          </div>
          {!pulse?.low_stock?.length ? (
            <EmptyState title="Stock levels healthy" description="No SKUs have crossed reorder thresholds." />
          ) : (
            <div className="space-y-2">
              {pulse.low_stock.map((item: any) => (
                <div key={item.product_id} className="p-3 rounded-xl bg-[#FEF3C7]/45 border border-[#FDE68A] flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-[#202B43]">{item.name}</div>
                    <div className="font-mono text-[11px] text-[#4E5D78]">{item.sku}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-[#991B1B]">
                      {Number(item.quantity_on_hand)} {item.unit} left
                    </div>
                    <div className="text-[11px] text-[#4E5D78]">Threshold: {Number(item.reorder_threshold)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold text-[#202B43]">Tasks Requiring Attention</h2>
            <Link to="/app/tasks" className="text-xs font-semibold text-[#3867E9] underline">All Tasks</Link>
          </div>
          {!pulse?.tasks_attention?.length ? (
            <EmptyState title="Inbox clear" description="Zero pending tasks assigned right now." />
          ) : (
            <div className="space-y-2">
              {pulse.tasks_attention.map((t: any) => (
                <div key={t.id} className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-[#202B43]">{t.title}</div>
                    <div className="text-[#4E5D78]">{t.assignee_name || 'Unassigned'}</div>
                  </div>
                  <Badge tone={t.priority === 'urgent' || t.priority === 'high' ? 'danger' : 'neutral'}>
                    {t.priority}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-base font-bold text-[#202B43]">Recent Operational Audit Trail</h2>
            <Link to="/app/security" className="text-xs font-semibold text-[#3867E9] underline">Security Logs</Link>
          </div>
          <div className="space-y-2">
            {(pulse?.recent_changes || []).map((ev: any) => (
              <div key={ev.id} className="p-2.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] flex items-center justify-between text-xs">
                <span className="font-mono font-semibold text-[#3867E9]">{ev.action}</span>
                <span className="text-[#4E5D78]">{ev.actor_name || 'System'}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export const IntelligencePage: React.FC<{ user: User }> = ({ user }) => {
  const { notify } = useToast();
  const [prompt, setPrompt] = useState('');
  const [history, setHistory] = useState<AiInteraction[]>([]);
  const [loading, setLoading] = useState(false);

  const loadHistory = async () => {
    try {
      setHistory(await api.getIntelligenceHistory());
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const ask = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      await api.askIntelligence(q, 'qa');
      setPrompt('');
      await loadHistory();
      notify('Grounded operational response logged cleanly.', 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Unable to execute AI query', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (id: string, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await api.approveAi(id);
      else await api.rejectAi(id);
      await loadHistory();
      notify(`AI suggestion ${action}d and audited.`, 'success');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Action denied', 'error');
    }
  };

  const canApprove = user.permissions.includes('ai:approve');

  return (
    <div className="space-y-6">
      <div>
        <Badge tone="mint">NEXORA Intelligence</Badge>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1.5">
          Grounded Business Assistant (Human in Control)
        </h1>
        <p className="text-sm text-[#4E5D78]">
          Answers only from your workspace’s authorized PostgreSQL records, displays citations, blocks prompt injection and requires human approval before consequential drafts take effect.
        </p>
      </div>

      <Card accent="mint" className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => ask(q)}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] text-xs font-semibold text-[#127466] hover:bg-[#E6F6F3] hover:border-[#99DDD2] transition-colors cursor-pointer"
            >
              {q}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(prompt);
          }}
          className="space-y-3"
        >
          <Textarea
            label="Ask NEXORA Intelligence about your business data"
            rows={3}
            placeholder="e.g. Which customers need follow-up this week or which SKUs are running low?"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-[#4E5D78]">
              All API keys stay server-side. Interactions are logged to <code className="font-mono">ai_interactions</code>.
            </span>
            <Button type="submit" loading={loading} leftIcon={<Send className="w-4 h-4" />}>
              Run Grounded Query
            </Button>
          </div>
        </form>
      </Card>

      <div className="space-y-4">
        <h2 className="font-heading text-lg font-bold text-[#202B43]">Interaction &amp; Approval Audit History</h2>
        {!history.length ? (
          <EmptyState
            icon={<Sparkles className="w-5 h-5" />}
            title="No AI queries logged yet"
            description="Select one of the example operational questions above to generate a cited workspace summary."
          />
        ) : (
          history.map((item) => (
            <Card key={item.id} className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-xs font-bold text-[#3867E9]">Q: {item.sanitized_prompt}</div>
                <div className="flex items-center gap-2">
                  <Badge tone="neutral">{item.provider_mode}</Badge>
                  <Badge
                    tone={
                      item.status === 'approved' || item.status === 'completed'
                        ? 'forest'
                        : item.status === 'rejected'
                        ? 'danger'
                        : 'warning'
                    }
                  >
                    {item.status}
                  </Badge>
                </div>
              </div>

              <pre className="whitespace-pre-wrap font-sans text-sm text-[#202B43] bg-[#F6F8FC] p-3.5 rounded-xl border border-[#E2E8F4]">
                {item.response_text}
              </pre>

              {!!item.grounded_sources_json?.length && (
                <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                  <span className="font-semibold text-[#4E5D78]">Sources:</span>
                  {item.grounded_sources_json.map((src, i) => (
                    <span key={`${src.table}-${i}`} className="px-2 py-0.5 rounded-md bg-[#EEF2FA] font-mono text-[#3867E9]">
                      {src.table}: {src.label}
                    </span>
                  ))}
                </div>
              )}

              {item.status === 'pending_approval' && canApprove && (
                <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F4]">
                  <Button
                    size="sm"
                    variant="secondary"
                    leftIcon={<XCircle className="w-3.5 h-3.5" />}
                    onClick={() => handleDecision(item.id, 'reject')}
                  >
                    Reject Draft
                  </Button>
                  <Button
                    size="sm"
                    variant="primary"
                    leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                    onClick={() => handleDecision(item.id, 'approve')}
                  >
                    Approve Suggestion
                  </Button>
                </div>
              )}
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
