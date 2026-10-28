import os
from pathlib import Path
from urllib.parse import quote_plus

import certifi
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Read .env if present (do not override already set system/Render environment variables)
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)
else:
    load_dotenv(override=False)

# Support unified DATABASE_URL (common in cloud hosts) or individual DB_* variables
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    print("Database configured via DATABASE_URL environment variable.")
else:
    DB_USER = os.getenv("DB_USER") or "2qvzCb4ckY28YTR.root"
    DB_PASSWORD = os.getenv("DB_PASSWORD") or "TkUlyIt79g9JLww0"
    DB_HOST = os.getenv("DB_HOST") or "gateway01.ap-northeast-1.prod.aws.tidbcloud.com"
    DB_PORT = os.getenv("DB_PORT") or "4000"
    DB_NAME = os.getenv("DB_NAME") or "customer_database"
    print(f"Connecting to database at {DB_HOST}:{DB_PORT} (database: {DB_NAME})")
    DATABASE_URL = (
        f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()
        except Exception:
            pass
else:
    # TiDB Cloud requires a secure (SSL) connection
    connect_args = {
        "connect_timeout": 20,
        "read_timeout": int(os.getenv("DB_READ_TIMEOUT", "180")),   # big uploads and a distant cloud database need more than 30 s
        "write_timeout": int(os.getenv("DB_WRITE_TIMEOUT", "180")),
    }
    if os.getenv("DB_SSL", "true").lower() == "true" or ("tidbcloud.com" in (locals().get("DB_HOST") or "")):
        connect_args["ssl"] = {"ca": certifi.where()}

    # pool_pre_ping + pool_recycle: TiDB Cloud closes idle connections, so test them before use and renew them every 5 minutes
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=240, pool_size=5, max_overflow=5,
                           pool_timeout=30, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
