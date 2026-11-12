import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Package,
  Plus,
  Printer,
  ShoppingCart,
  Sparkles,
  Truck,
  Warehouse,
  XCircle,
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
import { OrderSummary, Product, Supplier, User } from '../../types';

const STATUS_TONE: Record<string, 'neutral' | 'forest' | 'lime' | 'warning' | 'danger' | 'info'> = {
  draft: 'neutral',
  pending_approval: 'warning',
  confirmed: 'forest',
  packed: 'info',
  shipped: 'info',
  delivered: 'lime',
  cancelled: 'danger',
};

export const OrdersPage: React.FC<{ user: User }> = ({ user }) => {
  const toast = useToast();
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);

  // Order creation state
  const [customerId, setCustomerId] = useState('');
  const [discountAmount, setDiscountAmount] = useState('0');
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [rawText, setRawText] = useState('');
  const [sourceMessage, setSourceMessage] = useState('');
  const [unmatchedPhrases, setUnmatchedPhrases] = useState<string[]>([]);
  const [lineItems, setLineItems] = useState<Array<{ product_id: string; quantity: number }>>([]);
  const [submitting, setSubmitting] = useState(false);

  const canWrite = user.permissions.includes('orders:write');
  const canApprove = user.permissions.includes('orders:approve');

  const refresh = async (keepOrderId?: string) => {
    setLoading(true);
    try {
      const [ordData, custData, prodData] = await Promise.all([
        api.listOrders(),
        api.listCustomers(),
        api.listProducts(),
      ]);
      setOrders(ordData);
      setCustomers(custData);
      setProducts(prodData);
      if (custData.length > 0 && !customerId) setCustomerId(custData[0].id);
      if (prodData.length > 0 && lineItems.length === 0) {
        setLineItems([{ product_id: prodData[0].id, quantity: 1 }]);
      }
      if (keepOrderId) {
        const d = await api.getOrderDetail(keepOrderId);
        setSelectedOrder(d);
      }
    } catch (err: any) {
      toast.notify(err.message || 'Failed to load orders', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const filteredOrders = useMemo(() => {
    if (filterStatus === 'all') return orders;
    return orders.filter((o) => o.status === filterStatus);
  }, [orders, filterStatus]);

  const openDetail = async (id: string) => {
    try {
      const detail = await api.getOrderDetail(id);
      setSelectedOrder(detail);
    } catch (err: any) {
      toast.notify(err.message || 'Could not load order details', 'error');
    }
  };

  const handleExtractPreview = async () => {
    if (!rawText.trim()) return;
    try {
      const res = await api.extractOrderPreview(rawText);
      const matched = res.matched_lines || [];
      if (matched.length > 0) {
        setLineItems(
          matched.map((m: any) => ({
            product_id: m.product_id,
            quantity: Number(m.quantity) || 1,
          }))
        );
      }
      setUnmatchedPhrases(res.unmatched_phrases || []);
      setSourceMessage(rawText);
      toast.notify(
        matched.length > 0
          ? `Matched ${matched.length} product line(s). Review before saving.`
          : 'No SKU phrases matched directly; add lines manually.',
        matched.length > 0 ? 'success' : 'info'
      );
    } catch (err: any) {
      toast.notify(err.message || 'Extraction failed', 'error');
    }
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId || lineItems.length === 0) return;
    setSubmitting(true);
    try {
      const created = await api.createOrder({
        customer_id: customerId,
        items: lineItems.filter((li) => li.product_id && li.quantity > 0),
        discount_amount: Number(discountAmount) || 0,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        notes,
        source_message: sourceMessage,
      });
      toast.notify(`Order ${created.order_number} created in pending_approval.`, 'success');
      setCreateOpen(false);
      setRawText('');
      setSourceMessage('');
      setUnmatchedPhrases([]);
      setNotes('');
      await refresh(created.id);
    } catch (err: any) {
      toast.notify(err.message || 'Failed to create order', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirm = async (orderId: string) => {
    try {
      await api.confirmOrder(orderId);
      toast.notify('Order confirmed and inventory deducted atomically.', 'success');
      await refresh(orderId);
    } catch (err: any) {
      toast.notify(err.message || 'Order confirmation blocked (check stock).', 'error');
    }
  };

  const handleFulfilment = async (orderId: string, nextStatus: string) => {
    try {
      await api.updateOrderStatus(orderId, nextStatus);
      toast.notify(`Order updated to ${nextStatus}.`, 'success');
      await refresh(orderId);
    } catch (err: any) {
      toast.notify(err.message || 'Failed to update status', 'error');
    }
  };

  const handleCancel = async (orderId: string) => {
    try {
      await api.cancelOrder(orderId);
      toast.notify('Order cancelled and deducted inventory restored.', 'info');
      await refresh(orderId);
    } catch (err: any) {
      toast.notify(err.message || 'Cancellation failed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="forest">Orders &amp; Fulfilment</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            Sales Orders &amp; Atomic Stock Control
          </h1>
        </div>
        {canWrite && (
          <Button variant="primary" size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" /> New Sales Order
          </Button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {['all', 'pending_approval', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled'].map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold capitalize border transition-colors ${
              filterStatus === st
                ? 'bg-[#3867E9] text-white border-[#3867E9]'
                : 'bg-white text-[#4E5D78] border-[#E2E8F4] hover:bg-[#F6F8FC]'
            }`}
          >
            {st.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card className="lg:col-span-7 overflow-x-auto p-0">
          {loading ? (
            <div className="p-8 text-sm text-[#4E5D78]">Loading workspace orders...</div>
          ) : filteredOrders.length === 0 ? (
            <EmptyState
              icon={<ShoppingCart className="w-6 h-6" />}
              title="No matching orders"
              description="Create a new order manually or extract items from an incoming customer message."
              action={canWrite ? <Button size="sm" onClick={() => setCreateOpen(true)}>Create Order</Button> : undefined}
            />
          ) : (
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2E8F4] bg-[#F6F8FC] text-[#4E5D78] uppercase tracking-wider">
                  <th className="py-3 px-4">Order #</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Total ({user.tenant.currency})</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F4]">
                {filteredOrders.map((ord) => (
                  <tr
                    key={ord.id}
                    onClick={() => openDetail(ord.id)}
                    className={`cursor-pointer transition-colors hover:bg-[#F6F8FC] ${
                      selectedOrder?.id === ord.id ? 'bg-[#F3F6FE]' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-mono font-bold text-[#202B43]">{ord.order_number}</td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#202B43]">{ord.customer_name}</div>
                      <div className="text-[11px] text-[#4E5D78]">{ord.item_count} line(s)</div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge tone={STATUS_TONE[ord.status] || 'neutral'}>{ord.status.replace('_', ' ')}</Badge>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold tabular-nums">
                      {Number(ord.total_amount).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card className="lg:col-span-5 space-y-4">
          {!selectedOrder ? (
            <div className="py-12 text-center text-xs text-[#4E5D78]">
              Select any order row to inspect line items, live warehouse availability, approval actions, and printable tax summary.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start justify-between border-b border-[#E2E8F4] pb-3">
                <div>
                  <span className="font-mono text-xs text-[#4E5D78]">{selectedOrder.order_number}</span>
                  <h2 className="font-heading text-lg font-bold text-[#202B43]">{selectedOrder.customer_name}</h2>
                  <p className="text-xs text-[#4E5D78]">
                    {selectedOrder.customer_gstin ? `GSTIN: ${selectedOrder.customer_gstin} · ` : ''}
                    {selectedOrder.customer_phone || 'No phone'}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1.5">
                  <Badge tone={STATUS_TONE[selectedOrder.status] || 'neutral'}>
                    {selectedOrder.status.replace('_', ' ')}
                  </Badge>
                  <button
                    onClick={() => window.print()}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#3867E9] hover:underline"
                  >
                    <Printer className="w-3.5 h-3.5" /> Print Invoice
                  </button>
                </div>
              </div>

              {selectedOrder.source_message && (
                <div className="p-2.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] text-xs">
                  <div className="font-semibold text-[#3867E9] mb-0.5">Original Message Context</div>
                  <p className="text-[#4E5D78] whitespace-pre-wrap">{selectedOrder.source_message}</p>
                </div>
              )}

              <div className="space-y-2">
                <div className="text-xs font-bold uppercase tracking-wider text-[#4E5D78]">Line Items &amp; Stock Check</div>
                {(selectedOrder.items || []).map((it: any) => {
                  const lowForOrder =
                    selectedOrder.status === 'pending_approval' &&
                    Number(it.current_stock) < Number(it.quantity);
                  return (
                    <div
                      key={it.id}
                      className="p-2.5 rounded-xl border border-[#E2E8F4] flex items-center justify-between gap-2 text-xs"
                    >
                      <div>
                        <div className="font-semibold text-[#202B43]">
                          {it.product_name} <span className="font-mono text-[11px] text-[#4E5D78]">({it.sku})</span>
                        </div>
                        <div className="text-[11px] text-[#4E5D78]">
                          Qty: {it.quantity} × {user.tenant.currency} {Number(it.unit_price).toFixed(2)} (Tax {it.tax_rate}%)
                        </div>
                        {lowForOrder && (
                          <div className="text-[11px] font-semibold text-red-700 mt-0.5 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> Available stock: {it.current_stock} (insufficient)
                          </div>
                        )}
                      </div>
                      <div className="font-mono font-bold text-[#202B43] tabular-nums">
                        {Number(it.line_total).toFixed(2)}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-1 text-xs">
                <div className="flex justify-between text-[#4E5D78]">
                  <span>Subtotal</span>
                  <span className="font-mono">{user.tenant.currency} {Number(selectedOrder.subtotal).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-[#4E5D78]">
                  <span>Tax</span>
                  <span className="font-mono">{user.tenant.currency} {Number(selectedOrder.tax_amount).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-[#4E5D78]">
                  <span>Discount</span>
                  <span className="font-mono">-{user.tenant.currency} {Number(selectedOrder.discount_amount).toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-bold text-sm text-[#202B43] pt-1.5 border-t border-[#E2E8F4]">
                  <span>Grand Total</span>
                  <span className="font-mono">{user.tenant.currency} {Number(selectedOrder.total_amount).toFixed(2)}</span>
                </div>
              </div>

              {canApprove && (
                <div className="flex flex-wrap gap-2 pt-2">
                  {selectedOrder.status === 'pending_approval' && (
                    <Button variant="primary" size="sm" onClick={() => handleConfirm(selectedOrder.id)}>
                      <CheckCircle2 className="w-4 h-4 mr-1" /> Confirm &amp; Deduct Stock
                    </Button>
                  )}
                  {selectedOrder.status === 'confirmed' && (
                    <Button variant="secondary" size="sm" onClick={() => handleFulfilment(selectedOrder.id, 'packed')}>
                      <Package className="w-4 h-4 mr-1" /> Mark Packed
                    </Button>
                  )}
                  {selectedOrder.status === 'packed' && (
                    <Button variant="secondary" size="sm" onClick={() => handleFulfilment(selectedOrder.id, 'shipped')}>
                      <Truck className="w-4 h-4 mr-1" /> Mark Shipped
                    </Button>
                  )}
                  {selectedOrder.status === 'shipped' && (
                    <Button variant="primary" size="sm" onClick={() => handleFulfilment(selectedOrder.id, 'delivered')}>
                      <CheckCircle2 className="w-4 h-4 mr-1" /> Mark Delivered
                    </Button>
                  )}
                  {!['cancelled', 'delivered'].includes(selectedOrder.status) && (
                    <Button variant="danger" size="sm" onClick={() => handleCancel(selectedOrder.id)}>
                      <XCircle className="w-4 h-4 mr-1" /> Cancel &amp; Restore Stock
                    </Button>
                  )}
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create Sales Order">
        <form onSubmit={handleCreateOrder} className="space-y-4">
          <div className="p-3 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] space-y-2">
            <label className="block text-xs font-bold text-[#3867E9] flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Optional: Extract Order Lines from Message
            </label>
            <Textarea
              rows={2}
              placeholder="e.g. Please dispatch 10 Jasmine Rice 25kg and 5 Sunflower Oil 15L"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
            />
            <div className="flex items-center justify-between">
              <Button type="button" variant="secondary" size="sm" onClick={handleExtractPreview}>
                Extract SKUs
              </Button>
              {unmatchedPhrases.length > 0 && (
                <span className="text-[11px] text-amber-800">
                  Unmatched: {unmatchedPhrases.join(', ')}
                </span>
              )}
            </div>
          </div>

          <Select label="Customer" value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </Select>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-[#202B43]">Order Items</label>
              <button
                type="button"
                onClick={() =>
                  products[0] && setLineItems([...lineItems, { product_id: products[0].id, quantity: 1 }])
                }
                className="text-xs font-semibold text-[#3867E9] underline"
              >
                + Add Line
              </button>
            </div>
            {lineItems.map((li, idx) => (
              <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                <div className="col-span-8">
                  <select
                    value={li.product_id}
                    onChange={(e) => {
                      const next = [...lineItems];
                      next[idx].product_id = e.target.value;
                      setLineItems(next);
                    }}
                    className="w-full rounded-xl border border-[#E2E8F4] px-3 py-2 text-xs bg-white"
                  >
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.sku} · {p.name} (Stock: {p.quantity_on_hand})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-span-3">
                  <input
                    type="number"
                    min={1}
                    step="1"
                    value={li.quantity}
                    onChange={(e) => {
                      const next = [...lineItems];
                      next[idx].quantity = Number(e.target.value);
                      setLineItems(next);
                    }}
                    className="w-full rounded-xl border border-[#E2E8F4] px-2.5 py-2 text-xs bg-white"
                  />
                </div>
                <div className="col-span-1 text-right">
                  {lineItems.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setLineItems(lineItems.filter((_, i) => i !== idx))}
                      className="text-xs text-red-600 font-bold"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Discount Amount"
              type="number"
              min="0"
              step="0.01"
              value={discountAmount}
              onChange={(e) => setDiscountAmount(e.target.value)}
            />
            <Input
              label="Due Date"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>

          <Textarea
            label="Order Notes"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Delivery schedule or transporter notes"
          />

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" variant="primary" loading={submitting}>Save Draft Order</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export const ProductsPage: React.FC<{ user: User }> = ({ user }) => {
  const toast = useToast();
  const [products, setProducts] = useState<Product[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({
    sku: '',
    name: '',
    brand: '',
    category: 'Grains & Staples',
    unit: 'bag',
    unit_price: '0',
    cost_price: '0',
    tax_rate: '5',
    supplier_id: '',
    initial_stock: '0',
    reorder_threshold: '10',
    location: 'Main Warehouse',
  });

  const canWrite = user.permissions.includes('inventory:write');

  const refresh = () => {
    api.listProducts().then(setProducts).catch(() => {});
    api.listSuppliers().then(setSuppliers).catch(() => {});
  };

  useEffect(() => {
    refresh();
  }, []);

  const filtered = useMemo(
    () =>
      products.filter(
        (p) =>
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.sku.toLowerCase().includes(search.toLowerCase())
      ),
    [products, search]
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createProduct({
        ...form,
        unit_price: Number(form.unit_price),
        cost_price: Number(form.cost_price),
        tax_rate: Number(form.tax_rate),
        initial_stock: Number(form.initial_stock),
        reorder_threshold: Number(form.reorder_threshold),
        supplier_id: form.supplier_id || null,
      });
      toast.notify('SKU created and inventory initialized.', 'success');
      setModalOpen(false);
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Could not create SKU', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="forest">Product Catalog</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            SKUs, Pricing &amp; GST Rates
          </h1>
        </div>
        {canWrite && (
          <Button variant="primary" size="sm" onClick={() => setModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" /> Add Product SKU
          </Button>
        )}
      </div>

      <Card className="space-y-4">
        <div className="max-w-sm">
          <Input placeholder="Filter products by SKU or name..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E2E8F4] bg-[#F6F8FC] text-[#4E5D78] uppercase tracking-wider">
                <th className="py-3 px-3">SKU</th>
                <th className="py-3 px-3">Product</th>
                <th className="py-3 px-3">Category</th>
                <th className="py-3 px-3 text-right">Sell ({user.tenant.currency})</th>
                <th className="py-3 px-3 text-right">GST %</th>
                <th className="py-3 px-3 text-right">On Hand</th>
                <th className="py-3 px-3">Supplier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F4]">
              {filtered.map((p) => (
                <tr key={p.id} className="hover:bg-[#F6F8FC]">
                  <td className="py-3 px-3 font-mono font-semibold text-[#3867E9]">{p.sku}</td>
                  <td className="py-3 px-3">
                    <div className="font-semibold text-[#202B43]">{p.name}</div>
                    <div className="text-[11px] text-[#4E5D78]">{p.brand || 'House Brand'} · {p.unit}</div>
                  </td>
                  <td className="py-3 px-3 text-[#4E5D78]">{p.category}</td>
                  <td className="py-3 px-3 text-right font-mono tabular-nums">{Number(p.unit_price).toFixed(2)}</td>
                  <td className="py-3 px-3 text-right font-mono">{Number(p.tax_rate)}%</td>
                  <td className="py-3 px-3 text-right font-mono font-bold">
                    <span className={p.quantity_on_hand <= p.reorder_threshold ? 'text-amber-700' : 'text-[#202B43]'}>
                      {p.quantity_on_hand}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-[#4E5D78]">{p.supplier_name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add Product SKU">
        <form onSubmit={handleCreate} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Input label="SKU Code" required value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="SKU-RICE-25" />
            <Input label="Category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          </div>
          <Input label="Product Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-3 gap-3">
            <Input label="Unit Price" type="number" step="0.01" required value={form.unit_price} onChange={(e) => setForm({ ...form, unit_price: e.target.value })} />
            <Input label="Cost Price" type="number" step="0.01" value={form.cost_price} onChange={(e) => setForm({ ...form, cost_price: e.target.value })} />
            <Input label="Tax %" type="number" step="0.1" value={form.tax_rate} onChange={(e) => setForm({ ...form, tax_rate: e.target.value })} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Input label="Initial Stock" type="number" value={form.initial_stock} onChange={(e) => setForm({ ...form, initial_stock: e.target.value })} />
            <Input label="Reorder Point" type="number" value={form.reorder_threshold} onChange={(e) => setForm({ ...form, reorder_threshold: e.target.value })} />
            <Input label="Unit" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          </div>
          <Select label="Supplier (optional)" value={form.supplier_id} onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}>
            <option value="">None</option>
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </Select>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Create SKU</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export const InventoryPage: React.FC<{ user: User }> = ({ user }) => {
  const toast = useToast();
  const [items, setItems] = useState<any[]>([]);
  const [movements, setMovements] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [adjustItem, setAdjustItem] = useState<any | null>(null);
  const [adjForm, setAdjForm] = useState({ movement_type: 'in', quantity: '10', reason: '', reorder_threshold: '' });
  const [supOpen, setSupOpen] = useState(false);
  const [supForm, setSupForm] = useState({ name: '', contact_name: '', email: '', phone: '', lead_time_days: '4' });

  const canWrite = user.permissions.includes('inventory:write');

  const refresh = async () => {
    try {
      const [inv, sups] = await Promise.all([api.getInventory(), api.listSuppliers()]);
      setItems(inv.items || []);
      setMovements(inv.movements || []);
      setSuppliers(sups);
    } catch (err: any) {
      toast.notify(err.message || 'Failed to load inventory', 'error');
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const lowCount = items.filter((i) => i.is_low_stock).length;
  const totalVal = items.reduce((sum, i) => sum + Number(i.valuation || 0), 0);

  const handleAdjust = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustItem) return;
    try {
      await api.adjustInventory(adjustItem.product_id, {
        movement_type: adjForm.movement_type,
        quantity: Number(adjForm.quantity),
        reason: adjForm.reason,
        reorder_threshold: adjForm.reorder_threshold ? Number(adjForm.reorder_threshold) : null,
      });
      toast.notify('Inventory adjusted & stock movement logged.', 'success');
      setAdjustItem(null);
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Stock adjustment blocked', 'error');
    }
  };

  const handleCreateSupplier = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createSupplier({ ...supForm, lead_time_days: Number(supForm.lead_time_days) || 4 });
      toast.notify('Supplier added to workspace.', 'success');
      setSupOpen(false);
      setSupForm({ name: '', contact_name: '', email: '', phone: '', lead_time_days: '4' });
      refresh();
    } catch (err: any) {
      toast.notify(err.message || 'Failed to add supplier', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Badge tone="forest">Warehouse &amp; Stock</Badge>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-[#202B43] mt-1">
            Live Inventory &amp; Movement Ledger
          </h1>
        </div>
        {canWrite && (
          <Button variant="secondary" size="sm" onClick={() => setSupOpen(true)}>
            <Plus className="w-4 h-4 mr-1" /> Add Supplier
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatTile label="Active SKUs" value={items.length} icon={<Warehouse className="w-4 h-4" />} accent="forest" />
        <StatTile label="Low Stock Alerts" value={lowCount} detail="At or below threshold" accent={lowCount > 0 ? 'sand' : 'lime'} />
        <StatTile label="Cost Valuation" value={`${user.tenant.currency} ${Math.round(totalVal).toLocaleString()}`} accent="forest" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card className="lg:col-span-7 overflow-x-auto p-0">
          <div className="p-4 border-b border-[#E2E8F4] font-heading text-sm font-bold">Warehouse Stock Balances</div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-[#F6F8FC] border-b border-[#E2E8F4] text-[#4E5D78]">
                <th className="py-2.5 px-3">SKU / Name</th>
                <th className="py-2.5 px-3">Location</th>
                <th className="py-2.5 px-3 text-right">On Hand</th>
                <th className="py-2.5 px-3 text-right">Reorder At</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F4]">
              {items.map((it) => (
                <tr key={it.product_id} className="hover:bg-[#F6F8FC]">
                  <td className="py-2.5 px-3">
                    <div className="font-semibold text-[#202B43]">{it.name}</div>
                    <div className="font-mono text-[11px] text-[#4E5D78]">{it.sku}</div>
                  </td>
                  <td className="py-2.5 px-3 text-[#4E5D78]">{it.location}</td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold">
                    <Badge tone={it.is_low_stock ? 'warning' : 'lime'}>
                      {it.quantity_on_hand} {it.unit}
                    </Badge>
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-[#4E5D78]">{it.reorder_threshold}</td>
                  <td className="py-2.5 px-3 text-right">
                    {canWrite && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setAdjustItem(it);
                          setAdjForm({
                            movement_type: 'in',
                            quantity: '10',
                            reason: '',
                            reorder_threshold: String(it.reorder_threshold),
                          });
                        }}
                      >
                        Adjust
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-sm font-bold flex items-center gap-1.5">
              <ClipboardList className="w-4 h-4 text-[#3867E9]" /> Stock Movement Ledger
            </h2>
            <span className="text-[11px] text-[#4E5D78]">Immutable log</span>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {movements.map((m) => (
              <div key={m.id} className="p-2.5 rounded-xl bg-[#F6F8FC] border border-[#E2E8F4] text-xs flex justify-between gap-2">
                <div>
                  <div className="font-semibold text-[#202B43]">{m.product_name}</div>
                  <div className="text-[11px] text-[#4E5D78]">
                    {m.reason} · {m.actor_name || 'System'}
                  </div>
                </div>
                <div className="text-right font-mono">
                  <div className={Number(m.quantity_delta) >= 0 ? 'text-[#3867E9] font-bold' : 'text-red-700 font-bold'}>
                    {Number(m.quantity_delta) >= 0 ? '+' : ''}{m.quantity_delta}
                  </div>
                  <div className="text-[10px] text-[#4E5D78]">Bal: {m.quantity_after}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-[#E2E8F4]">
            <div className="text-xs font-bold uppercase tracking-wider text-[#4E5D78] mb-2">
              Workspace Suppliers ({suppliers.length})
            </div>
            <div className="space-y-1.5">
              {suppliers.map((s) => (
                <div key={s.id} className="text-xs flex justify-between text-[#202B43]">
                  <span className="font-medium">{s.name}</span>
                  <span className="text-[#4E5D78]">{s.lead_time_days}d lead</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <Modal open={!!adjustItem} onClose={() => setAdjustItem(null)} title={`Adjust Stock: ${adjustItem?.name || ''}`}>
        <form onSubmit={handleAdjust} className="space-y-3">
          <Select
            label="Movement Type"
            value={adjForm.movement_type}
            onChange={(e) => setAdjForm({ ...adjForm, movement_type: e.target.value })}
          >
            <option value="in">Stock In (Restock / Purchase)</option>
            <option value="out">Stock Out (Damage / Shrinkage)</option>
            <option value="adjustment">Exact Count Override</option>
          </Select>
          <Input
            label="Quantity"
            type="number"
            min="1"
            step="1"
            required
            value={adjForm.quantity}
            onChange={(e) => setAdjForm({ ...adjForm, quantity: e.target.value })}
          />
          <Input
            label="Reorder Threshold"
            type="number"
            min="0"
            value={adjForm.reorder_threshold}
            onChange={(e) => setAdjForm({ ...adjForm, reorder_threshold: e.target.value })}
          />
          <Input
            label="Audit Reason"
            required
            placeholder="e.g. Received PO #412 from Meridian Supply"
            value={adjForm.reason}
            onChange={(e) => setAdjForm({ ...adjForm, reason: e.target.value })}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setAdjustItem(null)}>Cancel</Button>
            <Button type="submit" variant="primary">Commit Stock Adjustment</Button>
          </div>
        </form>
      </Modal>

      <Modal open={supOpen} onClose={() => setSupOpen(false)} title="Add Supplier">
        <form onSubmit={handleCreateSupplier} className="space-y-3">
          <Input label="Supplier Name" required value={supForm.name} onChange={(e) => setSupForm({ ...supForm, name: e.target.value })} />
          <Input label="Contact Person" value={supForm.contact_name} onChange={(e) => setSupForm({ ...supForm, contact_name: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Email" value={supForm.email} onChange={(e) => setSupForm({ ...supForm, email: e.target.value })} />
            <Input label="Phone" value={supForm.phone} onChange={(e) => setSupForm({ ...supForm, phone: e.target.value })} />
          </div>
          <Input label="Lead Time (Days)" type="number" value={supForm.lead_time_days} onChange={(e) => setSupForm({ ...supForm, lead_time_days: e.target.value })} />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setSupOpen(false)}>Cancel</Button>
            <Button type="submit" variant="primary">Save Supplier</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
