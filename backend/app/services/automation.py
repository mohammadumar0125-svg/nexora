import json
from typing import Any, Dict

from app.services.audit import create_notification, record_audit_log
from sqlalchemy import text
from sqlalchemy.orm import Session


def evaluate_automation_trigger(
    db: Session,
    tenant_id: str,
    trigger_event: str,
    payload: Dict[str, Any],
    actor_user_id: str,
) -> int:
    """
    Evaluates active tenant workflows matching trigger_event.
    Queues human approval when requires_approval=True; executes safely when auto-approved.
    Returns count of triggered execution records.
    """
    workflows = db.execute(
        text(
            """
            SELECT id::text, name, action_type, action_config_json, requires_approval
            FROM automation_workflows
            WHERE tenant_id = :tid AND trigger_event = :ev AND is_active = TRUE
            """
        ),
        {"tid": tenant_id, "ev": trigger_event},
    ).mappings().all()

    count = 0
    for wf in workflows:
        status_val = "pending_approval" if wf["requires_approval"] else "executed"
        summary = (
            f"Queued workflow '{wf['name']}' awaiting human confirmation."
            if wf["requires_approval"]
            else f"Executed safe action '{wf['action_type']}' cleanly."
        )
        exec_row = db.execute(
            text(
                """
                INSERT INTO automation_executions (
                    tenant_id, workflow_id, status, trigger_payload_json, result_summary, executed_at
                )
                VALUES (
                    :tid, :wid, :st, CAST(:pl AS jsonb), :res,
                    CASE WHEN :st = 'executed' THEN NOW() ELSE NULL END
                )
                RETURNING id::text
                """
            ),
            {
                "tid": tenant_id,
                "wid": wf["id"],
                "st": status_val,
                "pl": json.dumps(payload, default=str),
                "res": summary,
            },
        ).mappings().first()

        if not wf["requires_approval"] and wf["action_type"] == "create_task":
            cfg = wf["action_config_json"] or {}
            title = cfg.get("task_title") or f"Follow up: {trigger_event}"
            db.execute(
                text(
                    """
                    INSERT INTO tasks (tenant_id, title, description, priority, status, created_by)
                    VALUES (:tid, :title, :desc, 'medium', 'todo', :actor)
                    """
                ),
                {"tid": tenant_id, "title": str(title)[:255], "desc": summary, "actor": actor_user_id},
            )

        create_notification(
            db,
            tenant_id=tenant_id,
            category="automation",
            title=f"Workflow: {wf['name']}",
            body=summary,
            entity_type="automation_execution",
            entity_id=exec_row["id"],
        )
        record_audit_log(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=f"automation_{status_val}",
            entity_type="automation_workflow",
            entity_id=wf["id"],
            after={"execution_id": exec_row["id"], "trigger_event": trigger_event},
            auto_commit=False,
        )
        count += 1
    return count
