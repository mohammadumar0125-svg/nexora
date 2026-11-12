import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.deps import AuthContext, get_auth_session, require_permission, verify_csrf
from app.services.audit import create_notification, record_audit_log
from app.services.storage import get_storage_provider, sanitize_filename
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import text

router = APIRouter(tags=["Pulse, Analytics, Tasks, Notifications & Files"])


class TaskIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    status: str = Field(default="todo", pattern="^(todo|in_progress|done)$")
    due_at: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    entity_type: str = Field(default="", max_length=40)
    entity_id: Optional[str] = None


@router.get("/pulse")
def get_business_pulse(
    _perm: AuthContext = Depends(require_permission("analytics:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db

    pending_orders = db.execute(
        text(
            """
            SELECT o.id::text, o.order_number, o.total_amount, o.status, o.created_at, c.name AS customer_name
            FROM orders o JOIN customers c ON c.id = o.customer_id
            WHERE o.tenant_id = :tid AND o.status IN ('draft', 'pending_approval')
            ORDER BY o.created_at DESC LIMIT 8
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    delayed_orders = db.execute(
        text(
            """
            SELECT o.id::text, o.order_number, o.status, o.due_date, o.total_amount, c.name AS customer_name
            FROM orders o JOIN customers c ON c.id = o.customer_id
            WHERE o.tenant_id = :tid AND o.status IN ('draft', 'pending_approval', 'confirmed', 'packed')
              AND o.due_date IS NOT NULL AND o.due_date < NOW()
            ORDER BY o.due_date ASC LIMIT 8
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    low_stock = db.execute(
        text(
            """
            SELECT p.id::text AS product_id, p.sku, p.name, i.quantity_on_hand, i.reorder_threshold, p.unit
            FROM inventory i JOIN products p ON p.id = i.product_id
            WHERE i.tenant_id = :tid AND p.active = TRUE AND i.quantity_on_hand <= i.reorder_threshold
            ORDER BY (i.quantity_on_hand - i.reorder_threshold) ASC LIMIT 8
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    followups = db.execute(
        text(
            """
            SELECT id::text, title, company_name, contact_name, stage, next_follow_up_at, estimated_value
            FROM leads
            WHERE tenant_id = :tid AND stage NOT IN ('won', 'lost')
            ORDER BY next_follow_up_at ASC NULLS LAST, created_at DESC LIMIT 8
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    tasks_attention = db.execute(
        text(
            """
            SELECT t.id::text, t.title, t.priority, t.status, t.due_at, u.full_name AS assignee_name
            FROM tasks t LEFT JOIN users u ON u.id = t.assigned_to_user_id
            WHERE t.tenant_id = :tid AND t.status <> 'done'
            ORDER BY CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, t.due_at ASC NULLS LAST
            LIMIT 8
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    recent_changes = db.execute(
        text(
            """
            SELECT al.id::text, al.action, al.entity_type, al.created_at, u.full_name AS actor_name
            FROM audit_logs al LEFT JOIN users u ON u.id = al.actor_user_id
            WHERE al.tenant_id = :tid
            ORDER BY al.created_at DESC LIMIT 6
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    recommendations = []
    if len(low_stock) > 0:
        recommendations.append(
            f"Replenish {len(low_stock)} SKU(s) currently at/below reorder thresholds ({low_stock[0]['name']})."
        )
    if len(pending_orders) > 0:
        recommendations.append(
            f"Review {len(pending_orders)} pending order(s) awaiting inventory allocation and confirmation."
        )
    if len(delayed_orders) > 0:
        recommendations.append(
            f"Follow up on {len(delayed_orders)} order(s) past target due dates."
        )
    if not recommendations:
        recommendations.append("Operations look balanced across stock levels and open order approvals.")

    return {
        "is_sample_workspace": ctx.tenant_is_sample,
        "summary": {
            "pending_orders_count": len(pending_orders),
            "delayed_orders_count": len(delayed_orders),
            "low_stock_count": len(low_stock),
            "followups_count": len(followups),
            "open_tasks_count": len(tasks_attention),
        },
        "pending_orders": [dict(r) for r in pending_orders],
        "delayed_orders": [dict(r) for r in delayed_orders],
        "low_stock": [dict(r) for r in low_stock],
        "followups": [dict(r) for r in followups],
        "tasks_attention": [dict(r) for r in tasks_attention],
        "recent_changes": [dict(r) for r in recent_changes],
        "recommendations": recommendations,
    }


@router.get("/analytics")
def get_analytics(
    days: int = Query(default=30, ge=1, le=365),
    _perm: AuthContext = Depends(require_permission("analytics:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    now = datetime.now(timezone.utc)
    start_curr = now - timedelta(days=days)
    start_prev = start_curr - timedelta(days=days)

    curr = db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE created_at >= :sc AND status <> 'cancelled') AS order_count,
                COALESCE(SUM(total_amount) FILTER (WHERE created_at >= :sc AND status <> 'cancelled'), 0) AS revenue,
                COUNT(*) FILTER (WHERE created_at >= :sc AND status IN ('confirmed', 'packed', 'shipped', 'delivered')) AS confirmed_orders
            FROM orders WHERE tenant_id = :tid
            """
        ),
        {"tid": ctx.tenant_id, "sc": start_curr},
    ).mappings().first()

    prev = db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE created_at >= :sp AND created_at < :sc AND status <> 'cancelled') AS order_count,
                COALESCE(SUM(total_amount) FILTER (WHERE created_at >= :sp AND created_at < :sc AND status <> 'cancelled'), 0) AS revenue
            FROM orders WHERE tenant_id = :tid
            """
        ),
        {"tid": ctx.tenant_id, "sp": start_prev, "sc": start_curr},
    ).mappings().first()

    customer_stats = db.execute(
        text(
            """
            SELECT COUNT(*) AS total_customers,
                   COUNT(*) FILTER (WHERE created_at >= :sc) AS new_customers_period
            FROM customers WHERE tenant_id = :tid
            """
        ),
        {"tid": ctx.tenant_id, "sc": start_curr},
    ).mappings().first()

    inv_stats = db.execute(
        text(
            """
            SELECT COUNT(*) AS sku_count,
                   COUNT(*) FILTER (WHERE i.quantity_on_hand <= i.reorder_threshold) AS low_stock_skus,
                   COUNT(*) FILTER (WHERE i.quantity_on_hand = 0) AS out_of_stock_skus,
                   COALESCE(SUM(i.quantity_on_hand * p.cost_price), 0) AS cost_valuation,
                   COALESCE(SUM(i.quantity_on_hand * p.unit_price), 0) AS retail_valuation
            FROM inventory i JOIN products p ON p.id = i.product_id
            WHERE i.tenant_id = :tid AND p.active = TRUE
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().first()

    task_stats = db.execute(
        text(
            """
            SELECT COUNT(*) FILTER (WHERE status = 'done') AS completed_tasks,
                   COUNT(*) FILTER (WHERE status <> 'done') AS open_tasks
            FROM tasks WHERE tenant_id = :tid
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().first()

    workflow_stats = db.execute(
        text(
            """
            SELECT COUNT(*) FILTER (WHERE status = 'executed') AS executed_runs,
                   COUNT(*) FILTER (WHERE status = 'pending_approval') AS pending_runs,
                   COUNT(*) FILTER (WHERE status = 'failed') AS failed_runs
            FROM automation_executions WHERE tenant_id = :tid
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().first()

    pipeline_by_stage = db.execute(
        text(
            """
            SELECT stage, COUNT(*) AS count, COALESCE(SUM(estimated_value), 0) AS value
            FROM leads WHERE tenant_id = :tid GROUP BY stage ORDER BY stage ASC
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    daily_series = db.execute(
        text(
            """
            SELECT to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD') AS day,
                   COUNT(*) AS orders,
                   COALESCE(SUM(total_amount), 0) AS revenue
            FROM orders
            WHERE tenant_id = :tid AND created_at >= :sc AND status <> 'cancelled'
            GROUP BY 1 ORDER BY 1 ASC
            """
        ),
        {"tid": ctx.tenant_id, "sc": start_curr},
    ).mappings().all()

    return {
        "is_sample_workspace": ctx.tenant_is_sample,
        "period_days": days,
        "definitions": {
            "revenue": "Sum of total_amount across non-cancelled tenant orders created within the selected period.",
            "confirmed_orders": "Orders confirmed, packed, shipped or delivered where atomic stock deduction succeeded.",
            "cost_valuation": "Sum of current quantity_on_hand multiplied by SKU cost_price.",
        },
        "current_period": dict(curr),
        "previous_period": dict(prev),
        "customers": dict(customer_stats),
        "inventory": dict(inv_stats),
        "tasks": dict(task_stats),
        "automation": dict(workflow_stats),
        "pipeline_by_stage": [dict(r) for r in pipeline_by_stage],
        "daily_series": [dict(r) for r in daily_series],
    }


@router.get("/reports/export")
def export_report_csv(
    report_type: str = Query(default="orders", pattern="^(orders|inventory|audit)$"),
    _perm: AuthContext = Depends(require_permission("analytics:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    buf = io.StringIO()
    w = csv.writer(buf)

    if report_type == "orders":
        rows = db.execute(
            text(
                "SELECT o.order_number, c.name AS customer, o.status, o.subtotal, o.tax_amount, o.total_amount, o.created_at FROM orders o JOIN customers c ON c.id = o.customer_id WHERE o.tenant_id = :tid ORDER BY o.created_at DESC"
            ),
            {"tid": ctx.tenant_id},
        ).mappings().all()
        w.writerow(["order_number", "customer", "status", "subtotal", "tax_amount", "total_amount", "created_at"])
        for r in rows:
            w.writerow([r["order_number"], r["customer"], r["status"], r["subtotal"], r["tax_amount"], r["total_amount"], r["created_at"]])
    elif report_type == "inventory":
        rows = db.execute(
            text(
                "SELECT p.sku, p.name, p.unit, i.quantity_on_hand, i.reorder_threshold, p.unit_price, p.cost_price FROM inventory i JOIN products p ON p.id = i.product_id WHERE i.tenant_id = :tid ORDER BY p.sku"
            ),
            {"tid": ctx.tenant_id},
        ).mappings().all()
        w.writerow(["sku", "name", "unit", "quantity_on_hand", "reorder_threshold", "unit_price", "cost_price"])
        for r in rows:
            w.writerow([r["sku"], r["name"], r["unit"], r["quantity_on_hand"], r["reorder_threshold"], r["unit_price"], r["cost_price"]])
    else:
        if "security:read" not in ctx.permissions:
            raise HTTPException(status_code=403, detail="security:read permission required for audit exports.")
        rows = db.execute(
            text("SELECT action, entity_type, entity_id, ip_address, created_at FROM audit_logs WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 500"),
            {"tid": ctx.tenant_id},
        ).mappings().all()
        w.writerow(["action", "entity_type", "entity_id", "ip_address", "created_at"])
        for r in rows:
            w.writerow([r["action"], r["entity_type"], r["entity_id"], r["ip_address"], r["created_at"]])

    record_audit_log(db, ctx.tenant_id, ctx.user_id, "report_exported", "report", report_type, ip_address=ctx.ip_address)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="nexora_{report_type}_report.csv"'},
    )


@router.get("/tasks")
def list_tasks(
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT t.id::text, t.title, t.description, t.priority, t.status, t.due_at,
                   t.assigned_to_user_id::text, u.full_name AS assignee_name,
                   t.entity_type, t.entity_id::text, t.created_at
            FROM tasks t LEFT JOIN users u ON u.id = t.assigned_to_user_id
            WHERE t.tenant_id = :tid
            ORDER BY (t.status = 'done') ASC, t.due_at ASC NULLS LAST, t.created_at DESC
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    req: TaskIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("tasks:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO tasks (tenant_id, title, description, priority, status, due_at, assigned_to_user_id, entity_type, entity_id, created_by)
            VALUES (:tid, :ti, :ds, :pr, :st, :du, :asg, :et, :eid, :uid)
            RETURNING id::text, title, description, priority, status, due_at, assigned_to_user_id::text, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "ti": req.title.strip(),
            "ds": req.description.strip(),
            "pr": req.priority,
            "st": req.status,
            "du": req.due_at or None,
            "asg": req.assigned_to_user_id or ctx.user_id,
            "et": req.entity_type.strip(),
            "eid": req.entity_id or None,
            "uid": ctx.user_id,
        },
    ).mappings().first()
    create_notification(
        db,
        ctx.tenant_id,
        title=f"New Task: {row['title']}",
        body=f"Priority {row['priority']} task created by {ctx.full_name}.",
        category="task",
        user_id=row["assigned_to_user_id"],
        entity_type="task",
        entity_id=row["id"],
    )
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "task_created", "task", row["id"], after={"title": row["title"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: str,
    req: TaskIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("tasks:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            UPDATE tasks SET title = :ti, description = :ds, priority = :pr, status = :st,
                             due_at = :du, assigned_to_user_id = :asg, updated_at = NOW()
            WHERE tenant_id = :tid AND id = :id
            RETURNING id::text, title, description, priority, status, due_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "id": task_id,
            "ti": req.title.strip(),
            "ds": req.description.strip(),
            "pr": req.priority,
            "st": req.status,
            "du": req.due_at or None,
            "asg": req.assigned_to_user_id or None,
        },
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "task_updated", "task", task_id, after={"status": row["status"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.get("/notifications")
def list_notifications(
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT id::text, category, title, body, entity_type, entity_id::text, is_read, created_at
            FROM notifications
            WHERE tenant_id = :tid AND (user_id IS NULL OR user_id = :uid)
            ORDER BY is_read ASC, created_at DESC LIMIT 50
            """
        ),
        {"tid": ctx.tenant_id, "uid": ctx.user_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: str,
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    db.execute(
        text("UPDATE notifications SET is_read = TRUE WHERE tenant_id = :tid AND id = :nid"),
        {"tid": ctx.tenant_id, "nid": notif_id},
    )
    db.commit()
    return {"status": "read"}


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    db.execute(
        text("UPDATE notifications SET is_read = TRUE WHERE tenant_id = :tid AND (user_id IS NULL OR user_id = :uid)"),
        {"tid": ctx.tenant_id, "uid": ctx.user_id},
    )
    db.commit()
    return {"status": "all_read"}


@router.get("/files")
def list_files(
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[str] = Query(default=None),
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT id::text, entity_type, entity_id::text, original_filename, mime_type, size_bytes, created_at
            FROM files
            WHERE tenant_id = :tid
              AND (:et IS NULL OR entity_type = :et)
              AND (:eid IS NULL OR entity_id::text = :eid)
            ORDER BY created_at DESC LIMIT 50
            """
        ),
        {"tid": ctx.tenant_id, "et": entity_type, "eid": entity_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/files/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    file: UploadFile = File(...),
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    content = await file.read()
    storage = get_storage_provider()
    stored = storage.put_object(ctx.tenant_id, content, file.content_type or "")
    safe_name = sanitize_filename(file.filename or "document")

    row = db.execute(
        text(
            """
            INSERT INTO files (tenant_id, entity_type, entity_id, original_filename, storage_key, mime_type, size_bytes, sha256, uploaded_by)
            VALUES (:tid, :et, :eid, :ofn, :sk, :mt, :sb, :sha, :uid)
            RETURNING id::text, original_filename, mime_type, size_bytes, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "et": entity_type[:40],
            "eid": entity_id,
            "ofn": safe_name,
            "sk": stored.storage_key,
            "mt": stored.mime_type,
            "sb": stored.size_bytes,
            "sha": stored.sha256,
            "uid": ctx.user_id,
        },
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "file_uploaded", entity_type, entity_id, after={"file_id": row["id"], "filename": safe_name}, ip_address=ctx.ip_address)
    return dict(row)


@router.get("/files/{file_id}/download")
def download_file(
    file_id: str,
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text("SELECT original_filename, storage_key, mime_type FROM files WHERE tenant_id = :tid AND id = :fid"),
        {"tid": ctx.tenant_id, "fid": file_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found in workspace.")
    storage = get_storage_provider()
    data = storage.read_object(ctx.tenant_id, row["storage_key"])
    return Response(
        content=data,
        media_type=row["mime_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{row["original_filename"]}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
