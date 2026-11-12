import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.seed_data import seed_database

def main():
    print("Initializing tables and seeding demo users...")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    print("Seed completed successfully! Demo owner and clerk ready.")

if __name__ == "__main__":
    main()
