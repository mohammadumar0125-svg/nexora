import json
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def record_audit_log(
    db: Session,
    tenant_id: str,
    actor_user_id: Optional[str],
    action: str,
    entity_type: str = "",
    entity_id: str = "",
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    ip_address: str = "",
    auto_commit: bool = True,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO audit_logs (tenant_id, actor_user_id, action, entity_type, entity_id, before_json, after_json, ip_address)
            VALUES (:tid, :actor, :act, :etype, :eid, CAST(:before_j AS jsonb), CAST(:after_j AS jsonb), :ip)
            """
        ),
        {
            "tid": tenant_id,
            "actor": actor_user_id,
            "act": action,
            "etype": entity_type,
            "eid": str(entity_id),
            "before_j": json.dumps(before, default=str) if before is not None else None,
            "after_j": json.dumps(after, default=str) if after is not None else None,
            "ip": ip_address[:64],
        },
    )
    if auto_commit:
        db.commit()


def create_notification(
    db: Session,
    tenant_id: str,
    title: str,
    body: str,
    category: str = "system",
    user_id: Optional[str] = None,
    entity_type: str = "",
    entity_id: Optional[str] = None,
    auto_commit: bool = False,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO notifications (tenant_id, user_id, category, title, body, entity_type, entity_id)
            VALUES (:tid, :uid, :cat, :title, :body, :etype, :eid)
            """
        ),
        {
            "tid": tenant_id,
            "uid": user_id,
            "cat": category[:40],
            "title": title[:255],
            "body": body,
            "etype": entity_type[:40],
            "eid": entity_id,
        },
    )
    if auto_commit:
        db.commit()
