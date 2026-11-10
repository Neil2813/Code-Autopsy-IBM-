"""
Reset DB — drops all tables and recreates them (empty schema).
Run from: D:\IBM BOB\Backend\
  python scripts/reset_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage.models import Base
from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "legacy_copilot.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

print(f"Resetting database: {DB_PATH}")
Base.metadata.drop_all(engine)
print("All tables dropped.")
Base.metadata.create_all(engine)
print("All tables recreated (empty).")

with engine.connect() as conn:
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
    print(f"\n{'Table':<35} {'Rows':>6}")
    print("-" * 44)
    for (tname,) in tables:
        count = conn.execute(text(f'SELECT COUNT(*) FROM "{tname}"')).scalar()
        print(f"  {tname:<33} {count:>6}")

print("\nDB reset complete — fresh start.")

