"""
Lavu — Database Connection
Uses SQLAlchemy with PostgreSQL.
For Supabase: replace DATABASE_URL with your Supabase connection string.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ↓ Set this in your .env file or Render/Railway environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:5p@u3VU3a3B2&c7@db.crjyiqeokflnjqfdnpgl.supabase.co:5432/postgres"
    # For Supabase, it looks like:
    # "postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres"
)

engine         = create_engine(DATABASE_URL)
SessionLocal   = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
