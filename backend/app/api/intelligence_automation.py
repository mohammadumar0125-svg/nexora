import json
from typing import Any, Dict, Optional

from app.core.deps import AuthContext, get_auth_session, require_permission, verify_csrf
from app.services.ai_intelligence import ask_nexora_intelligence
from app.services.audit import record_audit_log
from app.services.integrations import DEFAULT_INTEGRATIONS
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text

router = APIRouter(tags=["AI Intelligence, Automation, Settings & Security"])


class AiQuestionIn(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=2000)
    interaction_type: str = Field(default="qa", pattern="^(qa|summary|draft|recommendation)$")


class WorkflowIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str = Field(default="", max_length=1000)
    trigger_event: str = Field(..., pattern="^(order_confirmed|stock_low|lead_won|followup_overdue)$")
    action_type: str = Field(default="create_task", pattern="^(create_task|queue_notification|draft_followup)$")
    action_config: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True


class TenantSettingsIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=8)
    timezone: Optional[str] = Field(default=None, min_length=3, max_length=64)
    retention_days: Optional[int] = Field(default=None, ge=30, le=3650)
    tax_id: Optional[str] = Field(default=None, max_length=64)


class IntegrationConfigIn(BaseModel):
    status: str = Field(..., pattern="^(configured|not_configured|disabled)$")
    notes: str = Field(default="", max_length=500)


@router.post("/intelligence/ask")
def ask_intelligence(
    req: AiQuestionIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("ai:query")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    try:
        res = ask_nexora_intelligence(db, ctx.tenant_id, ctx.user_id, req.prompt, req.interaction_type)
        record_audit_log(
            db,
            ctx.tenant_id,
            ctx.user_id,
            "ai_interaction_created",
            "ai_interaction",
            res["id"],
            after={"provider_mode": res["provider_mode"], "status": res["status"]},
            ip_address=ctx.ip_address,
        )
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/intelligence/history")
def list_intelligence_history(
    _perm: AuthContext = Depends(require_permission("ai:query")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT ai.id::text, ai.interaction_type, ai.sanitized_prompt, ai.response_text,
                   ai.grounded_sources_json, ai.provider_mode, ai.requires_approval, ai.status,
                   ai.created_at, u.full_name AS actor_name
            FROM ai_interactions ai
            LEFT JOIN users u ON u.id = ai.user_id
            WHERE ai.tenant_id = :tid
            ORDER BY ai.created_at DESC LIMIT 30
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/intelligence/{interaction_id}/approve")
def approve_ai_action(
    interaction_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("ai:approve")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    updated = db.execute(
        text(
            """
            UPDATE ai_interactions SET status = 'approved', approved_by = :uid
            WHERE tenant_id = :tid AND id = :id AND status = 'pending_approval'
            RETURNING id::text, status
            """
        ),
        {"uid": ctx.user_id, "tid": ctx.tenant_id, "id": interaction_id},
    ).mappings().first()
    if not updated:
        raise HTTPException(status_code=404, detail="Pending AI interaction not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "ai_action_approved", "ai_interaction", interaction_id, ip_address=ctx.ip_address)
    return dict(updated)


@router.post("/intelligence/{interaction_id}/reject")
def reject_ai_action(
    interaction_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("ai:approve")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    updated = db.execute(
        text(
            """
            UPDATE ai_interactions SET status = 'rejected', approved_by = :uid
            WHERE tenant_id = :tid AND id = :id AND status = 'pending_approval'
            RETURNING id::text, status
            """
        ),
        {"uid": ctx.user_id, "tid": ctx.tenant_id, "id": interaction_id},
    ).mappings().first()
    if not updated:
        raise HTTPException(status_code=404, detail="Pending AI interaction not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "ai_action_rejected", "ai_interaction", interaction_id, ip_address=ctx.ip_address)
    return dict(updated)


@router.get("/automations")
def list_automations(
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    workflows = db.execute(
        text(
            """
            SELECT id::text, name, description, trigger_event, action_type, action_config_json,
                   requires_approval, is_active, created_at
            FROM automation_workflows
            WHERE tenant_id = :tid ORDER BY created_at DESC
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    executions = db.execute(
        text(
            """
            SELECT ae.id::text, ae.workflow_id::text, aw.name AS workflow_name, ae.status,
                   ae.result_summary, ae.retry_count, ae.error_message, ae.created_at, ae.executed_at
            FROM automation_executions ae
            JOIN automation_workflows aw ON aw.id = ae.workflow_id
            WHERE ae.tenant_id = :tid ORDER BY ae.created_at DESC LIMIT 40
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    return {"workflows": [dict(r) for r in workflows], "executions": [dict(r) for r in executions]}


@router.post("/automations", status_code=status.HTTP_201_CREATED)
def create_automation(
    req: WorkflowIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("automation:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO automation_workflows (
                tenant_id, name, description, trigger_event, action_type, action_config_json, requires_approval, created_by
            )
            VALUES (:tid, :nm, :ds, :te, :at, CAST(:ac AS jsonb), :ra, :uid)
            RETURNING id::text, name, description, trigger_event, action_type, requires_approval, is_active, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "nm": req.name.strip(),
            "ds": req.description.strip(),
            "te": req.trigger_event,
            "at": req.action_type,
            "ac": json.dumps(req.action_config),
            "ra": req.requires_approval,
            "uid": ctx.user_id,
        },
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "automation_created", "automation_workflow", row["id"], after={"name": row["name"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.patch("/automations/{workflow_id}/toggle")
def toggle_automation(
    workflow_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("automation:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            "UPDATE automation_workflows SET is_active = NOT is_active WHERE tenant_id = :tid AND id = :id RETURNING id::text, is_active"
        ),
        {"tid": ctx.tenant_id, "id": workflow_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "automation_toggled", "automation_workflow", workflow_id, after={"is_active": row["is_active"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.post("/automations/executions/{exec_id}/approve")
def approve_execution(
    exec_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("automation:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    ex = db.execute(
        text(
            """
            UPDATE automation_executions
            SET status = 'executed', approved_by = :uid, executed_at = NOW(),
                result_summary = 'Approved and executed by ' || :actor_name
            WHERE tenant_id = :tid AND id = :id AND status = 'pending_approval'
            RETURNING id::text, workflow_id::text, status, executed_at
            """
        ),
        {"uid": ctx.user_id, "actor_name": ctx.full_name, "tid": ctx.tenant_id, "id": exec_id},
    ).mappings().first()
    if not ex:
        raise HTTPException(status_code=404, detail="Pending execution not found.")
    wf = db.execute(
        text("SELECT name, action_type, action_config_json FROM automation_workflows WHERE tenant_id = :tid AND id = :wid"),
        {"tid": ctx.tenant_id, "wid": ex["workflow_id"]},
    ).mappings().first()
    if wf and wf["action_type"] == "create_task":
        cfg = wf["action_config_json"] or {}
        title = cfg.get("task_title") or f"Action: {wf['name']}"
        db.execute(
            text(
                "INSERT INTO tasks (tenant_id, title, description, priority, status, created_by) VALUES (:tid, :tl, :ds, 'high', 'todo', :uid)"
            ),
            {"tid": ctx.tenant_id, "tl": str(title)[:255], "ds": f"Created upon approval of workflow {wf['name']}", "uid": ctx.user_id},
        )
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "automation_execution_approved", "automation_execution", exec_id, ip_address=ctx.ip_address)
    return dict(ex)


@router.post("/automations/executions/{exec_id}/retry")
def retry_execution(
    exec_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("automation:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    ex = db.execute(
        text(
            """
            UPDATE automation_executions
            SET retry_count = retry_count + 1, status = 'executed', executed_at = NOW(),
                error_message = '', result_summary = 'Retried and completed cleanly.'
            WHERE tenant_id = :tid AND id = :id
            RETURNING id::text, status, retry_count, executed_at
            """
        ),
        {"tid": ctx.tenant_id, "id": exec_id},
    ).mappings().first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution record not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "automation_execution_retried", "automation_execution", exec_id, ip_address=ctx.ip_address)
    return dict(ex)


@router.get("/integrations")
def list_integrations(
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text("SELECT id::text, provider_key, category, name, status, config_json, updated_at FROM integrations WHERE tenant_id = :tid ORDER BY category, name"),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    if not rows:
        for d in DEFAULT_INTEGRATIONS:
            db.execute(
                text(
                    "INSERT INTO integrations (tenant_id, provider_key, category, name, status) VALUES (:tid, :pk, :cat, :nm, 'not_configured') ON CONFLICT DO NOTHING"
                ),
                {"tid": ctx.tenant_id, "pk": d["provider_key"], "cat": d["category"], "nm": d["name"]},
            )
        db.flush()
        rows = db.execute(
            text("SELECT id::text, provider_key, category, name, status, config_json, updated_at FROM integrations WHERE tenant_id = :tid ORDER BY category, name"),
            {"tid": ctx.tenant_id},
        ).mappings().all()
        db.commit()
    return [dict(r) for r in rows]


@router.patch("/integrations/{provider_key}")
def update_integration(
    provider_key: str,
    req: IntegrationConfigIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("settings:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            UPDATE integrations SET status = :st, config_json = CAST(:cfg AS jsonb), updated_at = NOW()
            WHERE tenant_id = :tid AND provider_key = :pk
            RETURNING id::text, provider_key, category, name, status, updated_at
            """
        ),
        {"st": req.status, "cfg": json.dumps({"notes": req.notes.strip()}), "tid": ctx.tenant_id, "pk": provider_key},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Integration connector not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "integration_updated", "integration", provider_key, after={"status": req.status}, ip_address=ctx.ip_address)
    return dict(row)


@router.get("/settings")
def get_tenant_settings(auth_and_db=Depends(get_auth_session)):
    ctx, db = auth_and_db
    row = db.execute(
        text("SELECT id::text, name, slug, currency, timezone, retention_days, tax_id, is_sample, created_at FROM tenants WHERE id = :tid"),
        {"tid": ctx.tenant_id},
    ).mappings().first()
    return dict(row)


@router.patch("/settings")
def update_tenant_settings(
    req: TenantSettingsIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("settings:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    curr = db.execute(
        text("SELECT name, currency, timezone, retention_days, tax_id FROM tenants WHERE id = :tid"),
        {"tid": ctx.tenant_id},
    ).mappings().first()
    new_vals = {
        "name": (req.name or curr["name"]).strip(),
        "currency": (req.currency or curr["currency"]).strip().upper(),
        "timezone": (req.timezone or curr["timezone"]).strip(),
        "retention_days": req.retention_days if req.retention_days is not None else curr["retention_days"],
        "tax_id": (req.tax_id if req.tax_id is not None else curr["tax_id"] or "").strip(),
    }
    row = db.execute(
        text(
            """
            UPDATE tenants
            SET name = :name, currency = :currency, timezone = :timezone, retention_days = :retention_days, tax_id = :tax_id, updated_at = NOW()
            WHERE id = :tid
            RETURNING id::text, name, slug, currency, timezone, retention_days, tax_id, is_sample
            """
        ),
        {**new_vals, "tid": ctx.tenant_id},
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "tenant_settings_updated", "tenant", ctx.tenant_id, before=dict(curr), after=new_vals, ip_address=ctx.ip_address)
    return dict(row)


@router.get("/security/audit-logs")
def get_audit_logs(
    _perm: AuthContext = Depends(require_permission("security:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT al.id::text, al.action, al.entity_type, al.entity_id, al.before_json, al.after_json,
                   al.ip_address, al.created_at, u.email AS actor_email, u.full_name AS actor_name
            FROM audit_logs al
            LEFT JOIN users u ON u.id = al.actor_user_id
            WHERE al.tenant_id = :tid
            ORDER BY al.created_at DESC LIMIT 100
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1, max_length=100),
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    pat = f"%{q.strip()}%"
    customers = db.execute(
        text("SELECT id::text, name AS title, category AS subtitle FROM customers WHERE tenant_id = :tid AND (name ILIKE :q OR phone ILIKE :q) LIMIT 5"),
        {"tid": ctx.tenant_id, "q": pat},
    ).mappings().all()
    orders = db.execute(
        text("SELECT id::text, order_number AS title, status AS subtitle FROM orders WHERE tenant_id = :tid AND order_number ILIKE :q LIMIT 5"),
        {"tid": ctx.tenant_id, "q": pat},
    ).mappings().all()
    products = db.execute(
        text("SELECT id::text, name AS title, sku AS subtitle FROM products WHERE tenant_id = :tid AND (name ILIKE :q OR sku ILIKE :q) LIMIT 5"),
        {"tid": ctx.tenant_id, "q": pat},
    ).mappings().all()
    leads = db.execute(
        text("SELECT id::text, title, company_name AS subtitle FROM leads WHERE tenant_id = :tid AND (title ILIKE :q OR company_name ILIKE :q) LIMIT 5"),
        {"tid": ctx.tenant_id, "q": pat},
    ).mappings().all()

    return {
        "customers": [{**dict(r), "route": "/app/customers"} for r in customers],
        "orders": [{**dict(r), "route": "/app/orders"} for r in orders],
        "products": [{**dict(r), "route": "/app/products"} for r in products],
        "leads": [{**dict(r), "route": "/app/leads"} for r in leads],
    }
