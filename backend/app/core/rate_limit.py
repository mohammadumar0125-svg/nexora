import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

# In-memory sliding window limiter for non-login API burst throttling
_API_BUCKETS: Dict[str, Deque[float]] = defaultdict(deque)


def check_api_rate_limit(bucket_key: str, max_requests: int = 60, window_seconds: int = 60) -> None:
    now = time.monotonic()
    q = _API_BUCKETS[bucket_key]
    while q and (now - q[0]) > window_seconds:
        q.popleft()
    if len(q) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please pause briefly and try again.",
            headers={"Retry-After": str(window_seconds)},
        )
    q.append(now)


def check_login_rate_limit(
    db: Session,
    key: str,
    max_attempts: int = 5,
    window_minutes: int = 15,
) -> Tuple[bool, Optional[datetime]]:
    now = datetime.now(timezone.utc)
    row = db.execute(
        text("SELECT attempts, first_attempt_at, locked_until FROM login_rate_limits WHERE limit_key = :k"),
        {"k": key},
    ).mappings().first()
    if not row:
        return True, None

    if row["locked_until"] and row["locked_until"] > now:
        return False, row["locked_until"]

    if (now - row["first_attempt_at"]) > timedelta(minutes=window_minutes):
        db.execute(
            text(
                "UPDATE login_rate_limits SET attempts = 0, first_attempt_at = NOW(), locked_until = NULL WHERE limit_key = :k"
            ),
            {"k": key},
        )
        db.commit()
        return True, None

    if row["attempts"] >= max_attempts:
        locked_until = now + timedelta(minutes=window_minutes)
        db.execute(
            text("UPDATE login_rate_limits SET locked_until = :lu WHERE limit_key = :k"),
            {"lu": locked_until, "k": key},
        )
        db.commit()
        return False, locked_until

    return True, None


def record_failed_login(
    db: Session,
    key: str,
    max_attempts: int = 5,
    window_minutes: int = 15,
) -> int:
    now = datetime.now(timezone.utc)
    row = db.execute(
        text("SELECT attempts, first_attempt_at FROM login_rate_limits WHERE limit_key = :k"),
        {"k": key},
    ).mappings().first()

    if not row:
        db.execute(
            text(
                "INSERT INTO login_rate_limits (limit_key, attempts, first_attempt_at) VALUES (:k, 1, NOW()) ON CONFLICT (limit_key) DO NOTHING"
            ),
            {"k": key},
        )
        db.commit()
        return 1

    if (now - row["first_attempt_at"]) > timedelta(minutes=window_minutes):
        attempts = 1
        locked_until = None
        db.execute(
            text(
                "UPDATE login_rate_limits SET attempts = 1, first_attempt_at = NOW(), locked_until = NULL WHERE limit_key = :k"
            ),
            {"k": key},
        )
    else:
        attempts = row["attempts"] + 1
        locked_until = (now + timedelta(minutes=window_minutes)) if attempts >= max_attempts else None
        db.execute(
            text("UPDATE login_rate_limits SET attempts = :a, locked_until = :lu WHERE limit_key = :k"),
            {"a": attempts, "lu": locked_until, "k": key},
        )
    db.commit()
    return attempts


def reset_login_rate_limit(db: Session, key: str) -> None:
    db.execute(text("DELETE FROM login_rate_limits WHERE limit_key = :k"), {"k": key})
    db.commit()
