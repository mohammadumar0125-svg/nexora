import {
  AiInteraction,
  Customer,
  Lead,
  NotificationItem,
  OrderSummary,
  Product,
  Supplier,
  TaskItem,
  User,
} from './types';

const API_BASE = '/api';
let csrfCache: string = sessionStorage.getItem('nexora_csrf') || '';

export function setCsrfToken(token: string) {
  csrfCache = token;
  if (token) sessionStorage.setItem('nexora_csrf', token);
  else sessionStorage.removeItem('nexora_csrf');
}

function hdrs(mutating = false): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (mutating && csrfCache) h['X-CSRF-Token'] = csrfCache;
  return h;
}

async function reqJson<T>(url: string, options: RequestInit = {}, mutating = false): Promise<T> {
  const headers: Record<string, string> = {
    ...hdrs(mutating),
    ...((options.headers as Record<string, string>) || {}),
  };
  const res = await fetch(url, { credentials: 'include', ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  // Public forms
  submitEarlyAccess: (payload: Record<string, string>) =>
    reqJson(`${API_BASE}/public/early-access`, { method: 'POST', body: JSON.stringify(payload) }),
  submitContact: (payload: Record<string, string>) =>
    reqJson(`${API_BASE}/public/contact`, { method: 'POST', body: JSON.stringify(payload) }),

  // Auth
  async registerWorkspace(payload: { company_name: string; full_name: string; email: string; password: string }) {
    const data = await reqJson<{ user: User; csrf_token: string; verification_token?: string }>(
      `${API_BASE}/auth/register`,
      { method: 'POST', body: JSON.stringify(payload) }
    );
    setCsrfToken(data.csrf_token);
    return data;
  },
  async login(email: string, password: string, totp_code?: string) {
    const data = await reqJson<{ mfa_required: boolean; user: User | null; csrf_token: string }>(
      `${API_BASE}/auth/login`,
      { method: 'POST', body: JSON.stringify({ email, password, totp_code }) }
    );
    if (data.csrf_token) setCsrfToken(data.csrf_token);
    return data;
  },
  async getMe(): Promise<User> {
    const u = await reqJson<User>(`${API_BASE}/auth/me`);
    if (u.csrf_token) setCsrfToken(u.csrf_token);
    return u;
  },
  async logout() {
    await reqJson(`${API_BASE}/auth/logout`, { method: 'POST' }, true).catch(() => {});
    setCsrfToken('');
  },
  async switchWorkspace(tenant_id: string) {
    const data = await reqJson<{ status: string; csrf_token: string }>(
      `${API_BASE}/auth/switch-workspace`,
      { method: 'POST', body: JSON.stringify({ tenant_id }) },
      true
    );
    if (data.csrf_token) setCsrfToken(data.csrf_token);
    return data;
  },
  forgotPassword: (email: string) =>
    reqJson<{ status: string; dev_reset_token?: string }>(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, new_password: string) =>
    reqJson(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ token, new_password }),
    }),
  verifyEmail: (token: string) =>
    reqJson(`${API_BASE}/auth/verify-email`, { method: 'POST', body: JSON.stringify({ token }) }),
  changePassword: (current_password: string, new_password: string) =>
    reqJson(`${API_BASE}/auth/change-password`, { method: 'POST', body: JSON.stringify({ current_password, new_password }) }, true),
  setupMfa: () => reqJson<{ secret: string; otpauth_uri: string }>(`${API_BASE}/auth/mfa/setup`, { method: 'POST' }, true),
  confirmMfa: (secret: string, totp_code: string) =>
    reqJson(`${API_BASE}/auth/mfa/confirm`, { method: 'POST', body: JSON.stringify({ secret, totp_code }) }, true),
  disableMfa: () => reqJson(`${API_BASE}/auth/mfa/disable`, { method: 'POST' }, true),
  listSessions: () => reqJson<any[]>(`${API_BASE}/auth/sessions`),
  revokeSession: (id: string) => reqJson(`${API_BASE}/auth/sessions/${id}`, { method: 'DELETE' }, true),

  // Team & Invitations
  getTeam: () => reqJson<{ members: any[]; invitations: any[]; roles: any[] }>(`${API_BASE}/team`),
  inviteMember: (email: string, role_code: string) =>
    reqJson<any>(`${API_BASE}/team/invite`, { method: 'POST', body: JSON.stringify({ email, role_code }) }, true),
  updateMembership: (userId: string, body: { role_code?: string; status?: string }) =>
    reqJson(`${API_BASE}/team/memberships/${userId}`, { method: 'PATCH', body: JSON.stringify(body) }, true),
  async acceptInvitation(payload: { token: string; full_name: string; password: string }) {
    const data = await reqJson<any>(`${API_BASE}/invitations/accept`, { method: 'POST', body: JSON.stringify(payload) });
    if (data.csrf_token) setCsrfToken(data.csrf_token);
    const user = await api.getMe();
    return { ...data, user };
  },

  // CRM
  listCustomers: (q?: string) =>
    reqJson<Customer[]>(`${API_BASE}/crm/customers${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  createCustomer: (payload: Partial<Customer>) =>
    reqJson<Customer>(`${API_BASE}/crm/customers`, { method: 'POST', body: JSON.stringify(payload) }, true),
  getCustomerDetail: (id: string) => reqJson<any>(`${API_BASE}/crm/customers/${id}`),
  updateCustomer: (id: string, payload: Partial<Customer>) =>
    reqJson<Customer>(`${API_BASE}/crm/customers/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }, true),
  importCustomersCsv: (csv_text: string) =>
    reqJson<{ imported_count: number }>(`${API_BASE}/crm/customers/import/csv`, { method: 'POST', body: JSON.stringify({ csv_text }) }, true),
  listContacts: () => reqJson<any[]>(`${API_BASE}/crm/contacts`),
  createContact: (payload: any) => reqJson(`${API_BASE}/crm/contacts`, { method: 'POST', body: JSON.stringify(payload) }, true),
  listLeads: () => reqJson<Lead[]>(`${API_BASE}/crm/leads`),
  createLead: (payload: any) => reqJson<Lead>(`${API_BASE}/crm/leads`, { method: 'POST', body: JSON.stringify(payload) }, true),
  updateLead: (id: string, payload: any) => reqJson<Lead>(`${API_BASE}/crm/leads/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }, true),
  convertLead: (id: string) => reqJson<any>(`${API_BASE}/crm/leads/${id}/convert`, { method: 'POST' }, true),
  logActivity: (payload: any) => reqJson(`${API_BASE}/crm/activities`, { method: 'POST', body: JSON.stringify(payload) }, true),
  addCustomerAlias: (payload: any) => reqJson(`${API_BASE}/crm/aliases`, { method: 'POST', body: JSON.stringify(payload) }, true),

  // Orders & Inventory
  listSuppliers: () => reqJson<Supplier[]>(`${API_BASE}/suppliers`),
  createSupplier: (payload: any) => reqJson<Supplier>(`${API_BASE}/suppliers`, { method: 'POST', body: JSON.stringify(payload) }, true),
  listProducts: () => reqJson<Product[]>(`${API_BASE}/products`),
  createProduct: (payload: any) => reqJson<Product>(`${API_BASE}/products`, { method: 'POST', body: JSON.stringify(payload) }, true),
  getInventory: () => reqJson<{ items: any[]; movements: any[] }>(`${API_BASE}/inventory`),
  adjustInventory: (productId: string, payload: any) =>
    reqJson(`${API_BASE}/inventory/${productId}/adjust`, { method: 'POST', body: JSON.stringify(payload) }, true),
  listOrders: () => reqJson<OrderSummary[]>(`${API_BASE}/orders`),
  getOrderDetail: (id: string) => reqJson<any>(`${API_BASE}/orders/${id}`),
  createOrder: (payload: any) => reqJson<any>(`${API_BASE}/orders`, { method: 'POST', body: JSON.stringify(payload) }, true),
  confirmOrder: (id: string) => reqJson(`${API_BASE}/orders/${id}/confirm`, { method: 'POST' }, true),
  updateOrderStatus: (id: string, status: string) =>
    reqJson(`${API_BASE}/orders/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }, true),
  cancelOrder: (id: string) => reqJson(`${API_BASE}/orders/${id}/cancel`, { method: 'POST' }, true),
  extractOrderPreview: (raw_text: string) =>
    reqJson<any>(`${API_BASE}/orders/extract-preview`, { method: 'POST', body: JSON.stringify({ raw_text }) }, true),

  // Pulse, Analytics, Tasks, Notifications, Files
  getPulse: () => reqJson<any>(`${API_BASE}/pulse`),
  getAnalytics: (days = 30) => reqJson<any>(`${API_BASE}/analytics?days=${days}`),
  listTasks: () => reqJson<TaskItem[]>(`${API_BASE}/tasks`),
  createTask: (payload: any) => reqJson<TaskItem>(`${API_BASE}/tasks`, { method: 'POST', body: JSON.stringify(payload) }, true),
  updateTask: (id: string, payload: any) => reqJson<TaskItem>(`${API_BASE}/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }, true),
  listNotifications: () => reqJson<NotificationItem[]>(`${API_BASE}/notifications`),
  markNotificationRead: (id: string) => reqJson(`${API_BASE}/notifications/${id}/read`, { method: 'POST' }, true),
  markAllNotificationsRead: () => reqJson(`${API_BASE}/notifications/read-all`, { method: 'POST' }, true),
  listFiles: (entityType: string, entityId: string) =>
    reqJson<any[]>(`${API_BASE}/files?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}`),
  async uploadFile(entityType: string, entityId: string, file: File) {
    const fd = new FormData();
    fd.append('entity_type', entityType);
    fd.append('entity_id', entityId);
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/files/upload`, {
      method: 'POST',
      credentials: 'include',
      headers: csrfCache ? { 'X-CSRF-Token': csrfCache } : {},
      body: fd,
    });
    if (!res.ok) {
      const b = await res.json().catch(() => ({}));
      throw new Error(b.detail || 'Upload failed');
    }
    return res.json();
  },

  // Intelligence, Automations, Settings, Security, Search
  askIntelligence: (prompt: string, interaction_type = 'qa') =>
    reqJson<any>(`${API_BASE}/intelligence/ask`, { method: 'POST', body: JSON.stringify({ prompt, interaction_type }) }, true),
  getIntelligenceHistory: () => reqJson<AiInteraction[]>(`${API_BASE}/intelligence/history`),
  approveAi: (id: string) => reqJson(`${API_BASE}/intelligence/${id}/approve`, { method: 'POST' }, true),
  rejectAi: (id: string) => reqJson(`${API_BASE}/intelligence/${id}/reject`, { method: 'POST' }, true),
  getAutomations: () => reqJson<{ workflows: any[]; executions: any[] }>(`${API_BASE}/automations`),
  createAutomation: (payload: any) => reqJson(`${API_BASE}/automations`, { method: 'POST', body: JSON.stringify(payload) }, true),
  toggleAutomation: (id: string) => reqJson(`${API_BASE}/automations/${id}/toggle`, { method: 'PATCH' }, true),
  approveExecution: (id: string) => reqJson(`${API_BASE}/automations/executions/${id}/approve`, { method: 'POST' }, true),
  retryExecution: (id: string) => reqJson(`${API_BASE}/automations/executions/${id}/retry`, { method: 'POST' }, true),
  listIntegrations: () => reqJson<any[]>(`${API_BASE}/integrations`),
  updateIntegration: (key: string, payload: { status: string; notes: string }) =>
    reqJson(`${API_BASE}/integrations/${key}`, { method: 'PATCH', body: JSON.stringify(payload) }, true),
  getSettings: () => reqJson<any>(`${API_BASE}/settings`),
  updateSettings: (payload: any) => reqJson(`${API_BASE}/settings`, { method: 'PATCH', body: JSON.stringify(payload) }, true),
  getAuditLogs: () => reqJson<any[]>(`${API_BASE}/security/audit-logs`),
  globalSearch: (q: string) => reqJson<any>(`${API_BASE}/search?q=${encodeURIComponent(q)}`),
};
