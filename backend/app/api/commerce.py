from typing import List, Optional

from app.core.deps import AuthContext, get_auth_session, require_permission, verify_csrf
from app.services.ai_intelligence import extract_order_message_lines
from app.services.audit import record_audit_log
from app.services.automation import evaluate_automation_trigger
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text

router = APIRouter(tags=["Orders & Inventory"])


class SupplierIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    contact_name: str = Field(default="", max_length=255)
    email: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=64)
    address: str = Field(default="", max_length=1000)
    lead_time_days: int = Field(default=5, ge=0, le=365)
    notes: str = Field(default="", max_length=2000)


class ProductIn(BaseModel):
    sku: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    brand: str = Field(default="", max_length=120)
    category: str = Field(default="General", max_length=120)
    unit: str = Field(default="unit", max_length=40)
    unit_price: float = Field(..., ge=0)
    cost_price: float = Field(default=0.0, ge=0)
    tax_rate: float = Field(default=5.0, ge=0, le=100)
    supplier_id: Optional[str] = None
    initial_stock: float = Field(default=0.0, ge=0)
    reorder_threshold: float = Field(default=10.0, ge=0)
    location: str = Field(default="Main Warehouse", max_length=120)


class StockAdjustmentIn(BaseModel):
    movement_type: str = Field(..., pattern="^(in|out|adjustment)$")
    quantity: float = Field(..., gt=0)
    reason: str = Field(..., min_length=2, max_length=500)
    reorder_threshold: Optional[float] = Field(default=None, ge=0)


class OrderItemInput(BaseModel):
    product_id: str
    quantity: float = Field(..., gt=0)


class OrderCreateIn(BaseModel):
    customer_id: str
    items: List[OrderItemInput] = Field(..., min_length=1)
    discount_amount: float = Field(default=0.0, ge=0)
    due_date: Optional[str] = None
    notes: str = Field(default="", max_length=2000)
    source_message: str = Field(default="", max_length=3000)


class OrderStatusIn(BaseModel):
    status: str = Field(..., pattern="^(packed|shipped|delivered)$")


class ExtractOrderTextIn(BaseModel):
    raw_text: str = Field(..., min_length=2, max_length=3000)


@router.get("/suppliers")
def list_suppliers(
    _perm: AuthContext = Depends(require_permission("inventory:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text("SELECT id::text, name, contact_name, email, phone, address, lead_time_days, notes, created_at FROM suppliers WHERE tenant_id = :tid ORDER BY name ASC"),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
def create_supplier(
    req: SupplierIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("inventory:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO suppliers (tenant_id, name, contact_name, email, phone, address, lead_time_days, notes)
            VALUES (:tid, :nm, :cn, :em, :ph, :ad, :lt, :nt)
            RETURNING id::text, name, contact_name, email, phone, address, lead_time_days, notes, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "nm": req.name.strip(),
            "cn": req.contact_name.strip(),
            "em": req.email.strip(),
            "ph": req.phone.strip(),
            "ad": req.address.strip(),
            "lt": req.lead_time_days,
            "nt": req.notes.strip(),
        },
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "supplier_created", "supplier", row["id"], after={"name": row["name"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.get("/products")
def list_products(
    _perm: AuthContext = Depends(require_permission("inventory:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT p.id::text, p.sku, p.name, p.brand, p.category, p.unit, p.unit_price, p.cost_price,
                   p.tax_rate, p.supplier_id::text, s.name AS supplier_name, p.active,
                   COALESCE(i.quantity_on_hand, 0) AS quantity_on_hand,
                   COALESCE(i.reorder_threshold, 10) AS reorder_threshold,
                   COALESCE(i.location, 'Main Warehouse') AS location
            FROM products p
            LEFT JOIN inventory i ON i.product_id = p.id AND i.tenant_id = p.tenant_id
            LEFT JOIN suppliers s ON s.id = p.supplier_id AND s.tenant_id = p.tenant_id
            WHERE p.tenant_id = :tid
            ORDER BY p.name ASC
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    req: ProductIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("inventory:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    dup = db.execute(
        text("SELECT 1 FROM products WHERE tenant_id = :tid AND lower(sku) = lower(:sku)"),
        {"tid": ctx.tenant_id, "sku": req.sku.strip()},
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail="Product SKU already exists in workspace.")

    prod = db.execute(
        text(
            """
            INSERT INTO products (tenant_id, sku, name, brand, category, unit, unit_price, cost_price, tax_rate, supplier_id)
            VALUES (:tid, :sku, :nm, :br, :cat, :un, :up, :cp, :tr, :sid)
            RETURNING id::text, sku, name, brand, category, unit, unit_price, cost_price, tax_rate
            """
        ),
        {
            "tid": ctx.tenant_id,
            "sku": req.sku.strip().upper(),
            "nm": req.name.strip(),
            "br": req.brand.strip(),
            "cat": req.category.strip(),
            "un": req.unit.strip(),
            "up": req.unit_price,
            "cp": req.cost_price,
            "tr": req.tax_rate,
            "sid": req.supplier_id or None,
        },
    ).mappings().first()

    db.execute(
        text(
            """
            INSERT INTO inventory (tenant_id, product_id, quantity_on_hand, reorder_threshold, location)
            VALUES (:tid, :pid, :qty, :rt, :loc)
            """
        ),
        {"tid": ctx.tenant_id, "pid": prod["id"], "qty": req.initial_stock, "rt": req.reorder_threshold, "loc": req.location.strip()},
    )
    if req.initial_stock > 0:
        db.execute(
            text(
                """
                INSERT INTO stock_movements (tenant_id, product_id, movement_type, quantity_delta, quantity_after, reference_type, reason, created_by)
                VALUES (:tid, :pid, 'in', :qd, :qa, 'opening_balance', 'Initial SKU balance', :uid)
                """
            ),
            {"tid": ctx.tenant_id, "pid": prod["id"], "qd": req.initial_stock, "qa": req.initial_stock, "uid": ctx.user_id},
        )
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "product_created", "product", prod["id"], after={"sku": prod["sku"]}, ip_address=ctx.ip_address)
    return {**dict(prod), "quantity_on_hand": req.initial_stock, "reorder_threshold": req.reorder_threshold}


@router.get("/inventory")
def list_inventory(
    _perm: AuthContext = Depends(require_permission("inventory:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    items = db.execute(
        text(
            """
            SELECT p.id::text AS product_id, p.sku, p.name, p.category, p.unit, p.unit_price, p.cost_price,
                   i.quantity_on_hand, i.reorder_threshold, i.location, i.updated_at,
                   (i.quantity_on_hand <= i.reorder_threshold) AS is_low_stock,
                   (i.quantity_on_hand * p.cost_price) AS valuation
            FROM inventory i
            JOIN products p ON p.id = i.product_id AND p.tenant_id = i.tenant_id
            WHERE i.tenant_id = :tid AND p.active = TRUE
            ORDER BY (i.quantity_on_hand <= i.reorder_threshold) DESC, p.name ASC
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    movements = db.execute(
        text(
            """
            SELECT sm.id::text, p.sku, p.name AS product_name, sm.movement_type, sm.quantity_delta,
                   sm.quantity_after, sm.reason, sm.created_at, u.full_name AS actor_name
            FROM stock_movements sm
            JOIN products p ON p.id = sm.product_id
            LEFT JOIN users u ON u.id = sm.created_by
            WHERE sm.tenant_id = :tid
            ORDER BY sm.created_at DESC LIMIT 50
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    return {"items": [dict(r) for r in items], "movements": [dict(r) for r in movements]}


@router.post("/inventory/{product_id}/adjust")
def adjust_inventory(
    product_id: str,
    req: StockAdjustmentIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("inventory:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    inv = db.execute(
        text("SELECT id::text, quantity_on_hand, reorder_threshold FROM inventory WHERE tenant_id = :tid AND product_id = :pid FOR UPDATE"),
        {"tid": ctx.tenant_id, "pid": product_id},
    ).mappings().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found.")

    curr = float(inv["quantity_on_hand"])
    if req.movement_type == "in":
        delta = float(req.quantity)
        new_qty = curr + delta
    elif req.movement_type == "out":
        delta = -float(req.quantity)
        new_qty = curr + delta
    else:
        new_qty = float(req.quantity)
        delta = new_qty - curr

    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Negative stock prevented: available={curr}, attempted deduction={abs(delta)}.",
        )

    new_thresh = req.reorder_threshold if req.reorder_threshold is not None else float(inv["reorder_threshold"])
    db.execute(
        text("UPDATE inventory SET quantity_on_hand = :nq, reorder_threshold = :rt, updated_at = NOW() WHERE id = :iid"),
        {"nq": new_qty, "rt": new_thresh, "iid": inv["id"]},
    )
    db.execute(
        text(
            """
            INSERT INTO stock_movements (tenant_id, product_id, movement_type, quantity_delta, quantity_after, reference_type, reason, created_by)
            VALUES (:tid, :pid, :mt, :qd, :qa, 'manual_adjustment', :rs, :uid)
            """
        ),
        {"tid": ctx.tenant_id, "pid": product_id, "mt": req.movement_type, "qd": delta, "qa": new_qty, "rs": req.reason.strip(), "uid": ctx.user_id},
    )
    if new_qty <= new_thresh:
        evaluate_automation_trigger(db, ctx.tenant_id, "stock_low", {"product_id": product_id, "quantity": new_qty}, ctx.user_id)
    record_audit_log(
        db,
        ctx.tenant_id,
        ctx.user_id,
        "inventory_adjusted",
        "inventory",
        product_id,
        before={"quantity": curr},
        after={"quantity": new_qty, "reason": req.reason.strip()},
        ip_address=ctx.ip_address,
    )
    return {"product_id": product_id, "quantity_on_hand": new_qty, "reorder_threshold": new_thresh}


@router.get("/orders")
def list_orders(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    _perm: AuthContext = Depends(require_permission("orders:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT o.id::text, o.order_number, o.customer_id::text, c.name AS customer_name, c.phone AS customer_phone,
                   o.status, o.subtotal, o.discount_amount, o.tax_amount, o.total_amount, o.due_date,
                   o.inventory_deducted, o.notes, o.created_at, o.approved_at,
                   (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id) AS item_count
            FROM orders o
            JOIN customers c ON c.id = o.customer_id AND c.tenant_id = o.tenant_id
            WHERE o.tenant_id = :tid AND (:st IS NULL OR o.status = :st)
            ORDER BY o.created_at DESC
            """
        ),
        {"tid": ctx.tenant_id, "st": status_filter or None},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    req: OrderCreateIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("orders:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    cust = db.execute(
        text("SELECT id::text, name FROM customers WHERE tenant_id = :tid AND id = :cid"),
        {"tid": ctx.tenant_id, "cid": req.customer_id},
    ).mappings().first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found in workspace.")

    # Monotonic tenant order number
    cnt = db.execute(
        text(
            """
            INSERT INTO tenant_counters (tenant_id, counter_name, last_value)
            VALUES (:tid, 'order_number', 1)
            ON CONFLICT (tenant_id, counter_name) DO UPDATE SET last_value = tenant_counters.last_value + 1
            RETURNING last_value
            """
        ),
        {"tid": ctx.tenant_id},
    ).scalar()
    order_number = f"ORD-{cnt:05d}"

    subtotal = 0.0
    tax_total = 0.0
    resolved_items = []
    for item in req.items:
        prod = db.execute(
            text(
                """
                SELECT p.id::text, p.sku, p.name, p.unit_price, p.tax_rate, COALESCE(i.quantity_on_hand, 0) AS stock
                FROM products p
                LEFT JOIN inventory i ON i.product_id = p.id AND i.tenant_id = p.tenant_id
                WHERE p.tenant_id = :tid AND p.id = :pid AND p.active = TRUE
                """
            ),
            {"tid": ctx.tenant_id, "pid": item.product_id},
        ).mappings().first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found.")
        line_sub = round(float(prod["unit_price"]) * float(item.quantity), 2)
        line_tax = round(line_sub * (float(prod["tax_rate"]) / 100.0), 2)
        subtotal += line_sub
        tax_total += line_tax
        resolved_items.append({
            "product_id": prod["id"],
            "product_name": prod["name"],
            "sku": prod["sku"],
            "quantity": item.quantity,
            "unit_price": float(prod["unit_price"]),
            "tax_rate": float(prod["tax_rate"]),
            "line_total": round(line_sub + line_tax, 2),
        })

    total_amount = max(0.0, round(subtotal + tax_total - req.discount_amount, 2))
    ord_row = db.execute(
        text(
            """
            INSERT INTO orders (
                tenant_id, order_number, customer_id, status, subtotal, discount_amount, tax_amount,
                total_amount, due_date, notes, source_message, created_by
            )
            VALUES (:tid, :onum, :cid, 'pending_approval', :sub, :disc, :tax, :tot, :dd, :nt, :sm, :uid)
            RETURNING id::text, order_number, status, subtotal, discount_amount, tax_amount, total_amount, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "onum": order_number,
            "cid": req.customer_id,
            "sub": round(subtotal, 2),
            "disc": round(req.discount_amount, 2),
            "tax": round(tax_total, 2),
            "tot": total_amount,
            "dd": req.due_date or None,
            "nt": req.notes.strip(),
            "sm": req.source_message.strip(),
            "uid": ctx.user_id,
        },
    ).mappings().first()

    for li in resolved_items:
        db.execute(
            text(
                """
                INSERT INTO order_items (tenant_id, order_id, product_id, product_name, sku, quantity, unit_price, tax_rate, line_total)
                VALUES (:tid, :oid, :pid, :pnm, :sku, :qty, :up, :tr, :lt)
                """
            ),
            {
                "tid": ctx.tenant_id,
                "oid": ord_row["id"],
                "pid": li["product_id"],
                "pnm": li["product_name"],
                "sku": li["sku"],
                "qty": li["quantity"],
                "up": li["unit_price"],
                "tr": li["tax_rate"],
                "lt": li["line_total"],
            },
        )

    record_audit_log(db, ctx.tenant_id, ctx.user_id, "order_created", "order", ord_row["id"], after={"order_number": order_number, "total": total_amount}, ip_address=ctx.ip_address)
    return {**dict(ord_row), "customer_name": cust["name"], "items": resolved_items}


@router.get("/orders/{order_id}")
def get_order_detail(
    order_id: str,
    _perm: AuthContext = Depends(require_permission("orders:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    ord_row = db.execute(
        text(
            """
            SELECT o.id::text, o.order_number, o.customer_id::text, c.name AS customer_name,
                   c.email AS customer_email, c.phone AS customer_phone, c.gstin AS customer_gstin,
                   c.billing_address AS customer_address, o.status, o.subtotal, o.discount_amount,
                   o.tax_amount, o.total_amount, o.due_date, o.notes, o.source_message,
                   o.inventory_deducted, o.created_at, o.approved_at
            FROM orders o
            JOIN customers c ON c.id = o.customer_id AND c.tenant_id = o.tenant_id
            WHERE o.tenant_id = :tid AND o.id = :oid
            """
        ),
        {"tid": ctx.tenant_id, "oid": order_id},
    ).mappings().first()
    if not ord_row:
        raise HTTPException(status_code=404, detail="Order not found.")

    items = db.execute(
        text(
            """
            SELECT oi.id::text, oi.product_id::text, oi.product_name, oi.sku, oi.quantity, oi.unit_price, oi.tax_rate, oi.line_total,
                   COALESCE(i.quantity_on_hand, 0) AS current_stock
            FROM order_items oi
            LEFT JOIN inventory i ON i.product_id = oi.product_id AND i.tenant_id = oi.tenant_id
            WHERE oi.tenant_id = :tid AND oi.order_id = :oid
            """
        ),
        {"tid": ctx.tenant_id, "oid": order_id},
    ).mappings().all()
    return {**dict(ord_row), "items": [dict(r) for r in items]}


@router.post("/orders/{order_id}/confirm")
def confirm_order(
    order_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("orders:approve")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    try:
        res = db.execute(
            text("SELECT * FROM confirm_order_atomic(:tid, :oid, :uid)"),
            {"tid": ctx.tenant_id, "oid": order_id, "uid": ctx.user_id},
        ).mappings().first()
        evaluate_automation_trigger(db, ctx.tenant_id, "order_confirmed", {"order_id": order_id}, ctx.user_id)
        low_hits = db.execute(
            text(
                """
                SELECT p.id::text AS product_id, p.name, i.quantity_on_hand
                FROM order_items oi
                JOIN inventory i ON i.product_id = oi.product_id AND i.tenant_id = oi.tenant_id
                JOIN products p ON p.id = oi.product_id
                WHERE oi.tenant_id = :tid AND oi.order_id = :oid AND i.quantity_on_hand <= i.reorder_threshold
                """
            ),
            {"tid": ctx.tenant_id, "oid": order_id},
        ).mappings().all()
        if low_hits:
            evaluate_automation_trigger(
                db,
                ctx.tenant_id,
                "stock_low",
                {"order_id": order_id, "products": [dict(h) for h in low_hits]},
                ctx.user_id,
            )
        db.commit()
        return dict(res)
    except Exception as exc:
        db.rollback()
        msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        if "Insufficient stock" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg.split("\n")[0])
        raise HTTPException(status_code=400, detail=msg.split("\n")[0])


@router.post("/orders/{order_id}/status")
def update_order_fulfilment(
    order_id: str,
    req: OrderStatusIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("orders:approve")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    ord_row = db.execute(
        text("SELECT status, order_number FROM orders WHERE tenant_id = :tid AND id = :oid"),
        {"tid": ctx.tenant_id, "oid": order_id},
    ).mappings().first()
    if not ord_row:
        raise HTTPException(status_code=404, detail="Order not found.")
    if ord_row["status"] in ("draft", "pending_approval", "cancelled"):
        raise HTTPException(status_code=400, detail="Order must be confirmed before advancing fulfilment status.")

    db.execute(
        text("UPDATE orders SET status = :st, updated_at = NOW() WHERE tenant_id = :tid AND id = :oid"),
        {"st": req.status, "tid": ctx.tenant_id, "oid": order_id},
    )
    record_audit_log(db, ctx.tenant_id, ctx.user_id, f"order_{req.status}", "order", order_id, after={"order_number": ord_row["order_number"], "status": req.status}, ip_address=ctx.ip_address)
    return {"order_id": order_id, "status": req.status}


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("orders:approve")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    try:
        db.execute(
            text("SELECT cancel_order_atomic(:tid, :oid, :uid, :rs)"),
            {"tid": ctx.tenant_id, "oid": order_id, "uid": ctx.user_id, "rs": f"Cancelled by {ctx.full_name}"},
        )
        db.commit()
        return {"order_id": order_id, "status": "cancelled"}
    except Exception as exc:
        db.rollback()
        msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        raise HTTPException(status_code=400, detail=msg.split("\n")[0])


@router.post("/orders/extract-preview")
def extract_order_preview(
    req: ExtractOrderTextIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("orders:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    skus = db.execute(
        text("SELECT id::text, sku, name, brand, unit_price, tax_rate FROM products WHERE tenant_id = :tid AND active = TRUE"),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    parsed = extract_order_message_lines(req.raw_text, [dict(r) for r in skus])
    return parsed
