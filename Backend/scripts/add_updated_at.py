"""Quick migration script to add updated_at column to analysis_results."""
from app.storage.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE analysis_results ADD COLUMN updated_at DATETIME"))
        conn.commit()
        print("Column added successfully")
    except Exception as e:
        print(f"Column may already exist: {e}")
