import os
from collections.abc import Generator

from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# RLS-enforced API Engine (connects as least-privilege api_role)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "5")),
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Administrative Owner Engine (strictly for migrations, seeding, and test harnesses)
owner_engine = create_engine(
    settings.MIGRATION_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=2,
    max_overflow=2,
    pool_recycle=300,
)
OwnerSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=owner_engine)


def get_unscoped_db() -> Generator[Session, None, None]:
    """
    Yields an api_role session with app.current_tenant_id explicitly cleared.
    FORCE ROW LEVEL SECURITY blocks all tenant table reads when unset.
    """
    db = SessionLocal()
    try:
        db.execute(text("SET LOCAL app.current_tenant_id = ''"))
        yield db
    finally:
        db.close()


def apply_rls_tenant(db: Session, tenant_id: str) -> None:
    """Applies PostgreSQL transaction-local tenant isolation variable."""
    db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": str(tenant_id)})
