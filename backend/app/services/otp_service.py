import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models import ResolutionOTP, Ticket

def hash_otp(code: str) -> str:
    """Computes SHA-256 hash of the 6-digit OTP."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def generate_resolution_otp(db: Session, ticket_id: int) -> Tuple[str, ResolutionOTP]:
    """
    Generates a secure cryptographically random 6-digit OTP,
    hashes it with SHA-256, and stores only the hash in the DB.
    Expires in 10 minutes. Max 5 attempts.
    Returns: (plain_otp_for_customer, otp_record)
    """
    # 6-digit numeric code
    plain_otp = f"{secrets.randbelow(900000) + 100000}"
    otp_hash = hash_otp(plain_otp)
    
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Invalidate any previous unused OTP for this ticket
    previous_otps = db.query(ResolutionOTP).filter(
        ResolutionOTP.ticket_id == ticket_id,
        ResolutionOTP.used == False
    ).all()
    for prev in previous_otps:
        prev.used = True

    record = ResolutionOTP(
        ticket_id=ticket_id,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        max_attempts=5,
        used=False
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return plain_otp, record

def verify_resolution_otp(db: Session, ticket_id: int, entered_code: str) -> Tuple[bool, str]:
    """
    Constant-time comparison verification.
    Checks:
    - active record exists
    - not used
    - not expired
    - attempt limit (<= 5)
    Returns: (is_valid, message)
    """
    now = datetime.now(timezone.utc)
    record = (
        db.query(ResolutionOTP)
        .filter(
            ResolutionOTP.ticket_id == ticket_id,
            ResolutionOTP.used == False
        )
        .order_by(ResolutionOTP.created_at.desc())
        .first()
    )

    if not record:
        return False, "No active resolution verification code found for this ticket."

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        return False, "Resolution verification code has expired. Please request a new code."

    if record.attempts >= record.max_attempts:
        return False, "Maximum verification attempts exceeded. Please request a new code."

    record.attempts += 1
    entered_hash = hash_otp(entered_code.strip())

    # Constant-time comparison
    if secrets.compare_digest(record.otp_hash, entered_hash):
        record.used = True
        db.commit()
        return True, "Code verified successfully."
    else:
        db.commit()
        remaining = record.max_attempts - record.attempts
        return False, f"Incorrect verification code. {remaining} attempt(s) remaining."
