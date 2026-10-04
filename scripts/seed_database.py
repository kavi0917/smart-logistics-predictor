"""Create tables, the demo user and sample shipments (safe to run more than once).

Usage (from project root):
    python scripts/seed_database.py            # seed only if the shipments table is empty
    python scripts/seed_database.py --reset    # DROP all tables first, then re-create and seed
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.services.seed_service import seed_all  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Seed the logistics database")
    parser.add_argument("--reset", action="store_true", help="drop all tables before seeding")
    args = parser.parse_args()

    init_db()
    if args.reset:
        Base.metadata.drop_all(bind=engine)
        init_db()
        print("All tables dropped and re-created.")
    db = SessionLocal()
    try:
        created = seed_all(db)
    finally:
        db.close()
    print(f"Seeding finished. Shipments created this run: {created}" if created else "Database already contains data - nothing to seed.")


if __name__ == "__main__":
    main()
