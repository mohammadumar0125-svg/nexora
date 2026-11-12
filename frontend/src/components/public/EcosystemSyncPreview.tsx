import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Users, ShoppingBag, Boxes, Activity, CheckCircle2, ArrowRight, Sparkles } from 'lucide-react';
import { Card, Badge } from '../ui';

interface SyncStep {
  id: string;
  label: string;
  title: string;
  actor: string;
  customerStatus: string;
  orderNumber: string;
  orderState: string;
  stockRemaining: number;
  pulseNote: string;
  aiNote: string;
}

const SYNC_STEPS: SyncStep[] = [
  {
    id: 'capture',
    label: '1. Customer Inquiry',
    title: 'Lead & Message Captured in CRM',
    actor: 'Sales Coordinator',
    customerStatus: 'Active Qualified Lead — Wholesale Distribution',
    orderNumber: 'Draft Pending',
    orderState: 'Draft Review',
    stockRemaining: 140,
    pulseNote: '1 follow-up task queued for today',
    aiNote: 'Sample draft parsed cleanly; waiting for team confirmation.',
  },
  {
    id: 'order',
    label: '2. Order Confirmed',
    title: 'Order Approved & Stock Locked',
    actor: 'Operations Manager',
    customerStatus: 'Verified Active Customer',
    orderNumber: 'ORD-2026-0104',
    orderState: 'Confirmed',
    stockRemaining: 120,
    pulseNote: '20 units reserved via transactional Postgres lock',
    aiNote: 'Audit entry logged; invoice summary ready.',
  },
  {
    id: 'fulfil',
    label: '3. Fulfilled & Updated',
    title: 'Inventory, Analytics & Business Pulse Synced',
    actor: 'Dispatch Team',
    customerStatus: 'Repeat Buyer Tier',
    orderNumber: 'ORD-2026-0104',
    orderState: 'Fulfilled',
    stockRemaining: 120,
    pulseNote: 'Revenue +12,400 INR recorded; reorder check passed',
    aiNote: 'Next reorder suggestion scheduled for +14 days (approval required).',
  },
];

export const EcosystemSyncPreview: React.FC = () => {
  const [stepIdx, setStepIdx] = useState(0);
  const current = SYNC_STEPS[stepIdx];

  return (
    <Card accent="cobalt" className="p-5 sm:p-6 bg-white border-[#E2E8F4] shadow-elevated space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#3867E9]">
            Illustrative Interactive Preview (Sample Scenario)
          </span>
          <h3 className="font-heading text-base font-bold text-[#202B43]">
            One connected action updates every workspace table
          </h3>
        </div>
        <Badge tone="champagne">Sample Sandbox</Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {SYNC_STEPS.map((step, idx) => (
          <button
            key={step.id}
            type="button"
            onClick={() => setStepIdx(idx)}
            className={`px-3 py-2.5 rounded-xl text-left text-xs font-semibold border transition-all duration-200 cursor-pointer ${
              idx === stepIdx
                ? 'bg-[#3867E9] text-white border-[#3867E9] shadow-sm'
                : 'bg-[#F6F8FC] text-[#4E5D78] border-[#E2E8F4] hover:bg-[#EEF2FA] hover:text-[#202B43]'
            }`}
          >
            <div className="flex items-center justify-between gap-1">
              <span>{step.label}</span>
              <ArrowRight className={`w-3.5 h-3.5 ${idx === stepIdx ? 'text-white' : 'opacity-40'}`} />
            </div>
          </button>
        ))}
      </div>

      <motion.div
        key={current.id}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
        className="grid grid-cols-1 sm:grid-cols-2 gap-3"
      >
        <div className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#3867E9]">
            <Users className="w-4 h-4" />
            <span>CRM Account</span>
          </div>
          <div className="text-sm font-bold text-[#202B43]">Meridian Retail Group (Sample)</div>
          <div className="text-xs text-[#4E5D78]">{current.customerStatus}</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#3867E9]">
            <ShoppingBag className="w-4 h-4" />
            <span>Order State</span>
          </div>
          <div className="text-sm font-bold text-[#202B43] font-mono">{current.orderNumber}</div>
          <div className="text-xs text-[#4E5D78]">Status: <strong className="text-[#3867E9]">{current.orderState}</strong></div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#8A5B14]">
            <Boxes className="w-4 h-4 text-[#D69B42]" />
            <span>Inventory Stock</span>
          </div>
          <div className="text-sm font-bold text-[#202B43] tabular-nums">
            {current.stockRemaining} Units On Hand
          </div>
          <div className="text-xs text-[#4E5D78]">Atomic SQL lock prevents negative stock</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#F3F6FE] border border-[#C5D5FA] space-y-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#3867E9]">
            <Activity className="w-4 h-4" />
            <span>Business Pulse</span>
          </div>
          <div className="text-sm font-bold text-[#202B43]">{current.title}</div>
          <div className="text-xs text-[#4E5D78]">{current.pulseNote}</div>
        </div>
      </motion.div>

      <div className="flex items-start gap-2.5 px-3.5 py-2.5 rounded-xl bg-[#E6F6F3]/80 border border-[#99DDD2] text-xs text-[#127466]">
        <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-[#22A995]" />
        <div className="flex-1">
          <span className="font-semibold">Human-Controlled AI Note:</span> {current.aiNote}
        </div>
        <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-[#22A995]" />
      </div>
    </Card>
  );
};
