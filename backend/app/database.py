import socket
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Ensure neon.tech connects even if local ISP DNS refuses resolution
if "neon.tech" in db_url and "hostaddr=" not in db_url:
    try:
        host = db_url.split("@")[1].split("/")[0].split("?")[0]
        socket.gethostbyname(host)
    except Exception:
        # Fallback to direct AWS Singapore IP for neon.tech pooler
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}hostaddr=13.228.184.177"

engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / NeonDB connection configuration
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    db_url,
    echo=False,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
