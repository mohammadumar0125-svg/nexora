export interface TenantInfo {
  id: string;
  name: string;
  slug: string;
  currency: string;
  is_sample: boolean;
}

export interface WorkspaceMembershipSummary {
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
  role_code: string;
  is_sample: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role_code: string;
  permissions: string[];
  is_email_verified: boolean;
  mfa_enabled: boolean;
  tenant: TenantInfo;
  workspaces: WorkspaceMembershipSummary[];
  csrf_token: string;
}

export interface Customer {
  id: string;
  name: string;
  category: string;
  email: string;
  phone: string;
  gstin: string;
  billing_address: string;
  status: string;
  language_hints: string;
  owner_name?: string;
  order_count?: number;
  total_spent?: number;
  created_at: string;
}

export interface Lead {
  id: string;
  title: string;
  company_name: string;
  contact_name: string;
  email: string;
  phone: string;
  source: string;
  stage: 'new' | 'contacted' | 'qualified' | 'proposal' | 'won' | 'lost';
  estimated_value: number;
  customer_id?: string | null;
  next_follow_up_at?: string | null;
  owner_name?: string;
  created_at: string;
}

export interface Supplier {
  id: string;
  name: string;
  contact_name: string;
  email: string;
  phone: string;
  address: string;
  lead_time_days: number;
  notes: string;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  brand: string;
  category: string;
  unit: string;
  unit_price: number;
  cost_price: number;
  tax_rate: number;
  supplier_id?: string | null;
  supplier_name?: string | null;
  active: boolean;
  quantity_on_hand: number;
  reorder_threshold: number;
  location: string;
}

export interface OrderSummary {
  id: string;
  order_number: string;
  customer_id: string;
  customer_name: string;
  customer_phone?: string;
  status: 'draft' | 'pending_approval' | 'confirmed' | 'packed' | 'shipped' | 'delivered' | 'cancelled';
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  due_date?: string | null;
  inventory_deducted: boolean;
  notes: string;
  created_at: string;
  item_count: number;
}

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'todo' | 'in_progress' | 'done';
  due_at?: string | null;
  assignee_name?: string | null;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  category: string;
  title: string;
  body: string;
  entity_type: string;
  entity_id?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface AiInteraction {
  id: string;
  interaction_type: string;
  sanitized_prompt: string;
  response_text: string;
  grounded_sources_json: Array<{ table: string; id: string; label: string }>;
  provider_mode: string;
  requires_approval: boolean;
  status: string;
  actor_name?: string;
  created_at: string;
}
