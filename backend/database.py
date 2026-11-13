"""
CustomerVault Database Engine & Session Provider
Manages connections to remote MySQL / TiDB Cloud or local SQLite fallback.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

import certifi
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base

# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Load Environment Configuration (.env):
# Checks if a local .env file exists in the backend directory and loads it.
# `override=False` ensures that production environment variables set by host
# providers (e.g. Render, Netlify, Railway, or Linux system variables) take
# precedence over local developer defaults.
# ==============================================================================
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)
else:
    load_dotenv(override=False)

# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Database Connection String Construction:
# Supports either a single unified DATABASE_URL (standard for cloud databases)
# or individual connection parameters (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME).
# Encodes special characters in passwords and prepends the PyMySQL driver name.
# ==============================================================================
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


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# SQLite Fallback Engine Builder:
# Used when offline, during tests, or when remote TiDB Cloud is unreachable:
# 1. Enables Write-Ahead Logging (WAL) for high concurrency and crash resilience.
# 2. Configures synchronous mode to NORMAL for speed.
# 3. Increases busy_timeout to 30,000ms so concurrent requests queue without 'database locked' errors.
# 4. Defines custom SQL functions (date_format, left) to emulate MySQL functions.
# ==============================================================================
def _build_sqlite_engine(db_path):
    connect_args = {"check_same_thread": False, "timeout": 30}
    eng = create_engine(f"sqlite:///{db_path}", connect_args=connect_args)

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()
        except Exception:
            pass
        if hasattr(dbapi_connection, "create_function"):
            try:
                import datetime
                def _date_format(val, fmt):
                    if val is None:
                        return None
                    if isinstance(val, (datetime.date, datetime.datetime)):
                        return val.strftime(fmt)
                    try:
                        dt = datetime.datetime.fromisoformat(str(val).split()[0])
                        return dt.strftime(fmt)
                    except Exception:
                        return str(val)
                dbapi_connection.create_function("date_format", 2, _date_format)
                dbapi_connection.create_function("left", 2, lambda s, n: str(s)[:n] if s is not None else None)
            except Exception:
                pass
    return eng


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Robust Database Engine Creator:
# Attempts to establish a pooled SSL connection to the primary database (TiDB Cloud / MySQL).
# Performs an immediate ping test (`SELECT 1`). If the remote host is unreachable
# (e.g. no internet connection, SSL negotiation fail, or firewall block), it catches
# the exception and gracefully switches the app to a local SQLite database (`customervault.db`)
# so the application remains operable without crashing.
# ==============================================================================
def _create_robust_engine():
    global DATABASE_URL
    if DATABASE_URL.startswith("sqlite"):
        sqlite_file = DATABASE_URL.replace("sqlite:///", "")
        return _build_sqlite_engine(sqlite_file)

    # TiDB Cloud requires a secure SSL connection using system root certificates
    connect_args = {
        "connect_timeout": 5,
        "read_timeout": int(os.getenv("DB_READ_TIMEOUT", "30")),
        "write_timeout": int(os.getenv("DB_WRITE_TIMEOUT", "30")),
    }
    if os.getenv("DB_SSL", "true").lower() == "true" or ("tidbcloud.com" in (locals().get("DB_HOST") or "")):
        connect_args["ssl"] = {"ca": certifi.where()}

    # Initialize SQLAlchemy connection pool with pre-ping validation and recycle timeouts
    eng = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=240,
        pool_size=5,
        max_overflow=5,
        pool_timeout=10,
        connect_args=connect_args
    )
    try:
        # Test connection validity safely without hanging or raising unhandled rollback exceptions
        conn = eng.connect()
        try:
            conn.execute(text("SELECT 1"))
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return eng
    except (Exception, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        print(f"Notice: Remote database at gateway01.ap-northeast-1.prod.aws.tidbcloud.com unreachable ({type(e).__name__}: {e}).")
        print("Gracefully falling back to local SQLite database at backend/customervault.db")
        sqlite_path = (Path(__file__).parent / "customervault.db").resolve()
        DATABASE_URL = f"sqlite:///{sqlite_path}"
        return _build_sqlite_engine(sqlite_path)


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Global Engine, Session Factory, and Declarative Base:
# - `engine`: The global active SQLAlchemy database engine.
# - `SessionLocal`: Session factory callable generating thread-isolated sessions.
# - `Base`: Common declarative base model from which all ORM entities inherit.
# ==============================================================================
engine = _create_robust_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# FastAPI Dependency: get_db()
# Provides a scoped SQLAlchemy database session per incoming HTTP request:
# Yields the active session to route handlers, then automatically closes the
# session in the `finally` block to return the connection back to the pool.
# ==============================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
