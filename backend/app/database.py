import os
import socket
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

def get_engine():
    # Read fresh from os.environ or settings so tests and commands can override DATABASE_URL dynamically
    db_url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Ensure neon.tech connects even if local ISP DNS refuses resolution
    if "neon.tech" in db_url and "hostaddr=" not in db_url:
        try:
            host = db_url.split("@")[1].split("/")[0].split("?")[0]
            socket.gethostbyname(host)
        except Exception:
            separator = "&" if "?" in db_url else "?"
            db_url = f"{db_url}{separator}hostaddr=13.228.184.177"

    engine_kwargs = {}
    if db_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 300

    return create_engine(db_url, echo=False, **engine_kwargs)

engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
