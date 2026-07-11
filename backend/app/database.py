from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
import shutil
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Get absolute path to database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_database_url() -> str:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url

    bundled_db_path = os.path.join(BASE_DIR, "internship.db")

    if os.getenv("VERCEL") == "1":
        runtime_db_path = os.path.join(tempfile.gettempdir(), "internship.db")
        if os.path.exists(bundled_db_path) and not os.path.exists(runtime_db_path):
            shutil.copy2(bundled_db_path, runtime_db_path)
        return f"sqlite:///{runtime_db_path}"

    return f"sqlite:///{bundled_db_path}"


DATABASE_URL = resolve_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
