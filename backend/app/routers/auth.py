from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Customer
from app.schemas import (
    UserRegister, UserLogin, GoogleLoginRequest, TokenResponse,
    UserOut, UserProfileUpdate, UserRoleUpdate
)
from app.services.auth_service import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    get_current_user, require_roles, determine_user_role, verify_google_id_token,
    normalize_role
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    clean_email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    # Determine role securely — nobody can self-promote to ADMIN/TECHNICIAN
    assigned_role = determine_user_role(clean_email, payload.role)

    # If registering as customer, link or create Customer record
    customer_id = None
    if assigned_role == "CUSTOMER":
        cust = db.query(Customer).filter((Customer.email == clean_email) | (Customer.phone == payload.phone)).first()
        if not cust:
            cust = Customer(
                name=payload.name,
                phone=payload.phone or f"+1-555-REG-{clean_email[:4]}",
                email=clean_email,
                address=payload.address
            )
            db.add(cust)
            db.flush()
        customer_id = cust.id

    hashed = hash_password(payload.password)
    user = User(
        email=clean_email,
        hashed_password=hashed,
        name=payload.name,
        role=assigned_role,
        phone=payload.phone,
        address=payload.address,
        customer_id=customer_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    clean_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support."
        )

    access_token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Google Identity Services login.
    Verifies ID token with google-auth, links existing customers by email,
    respects role allowlists, and returns application JWT.
    """
    id_info = verify_google_id_token(payload.id_token)
    google_id = id_info.get("sub")
    email = id_info.get("email", "").lower().strip()
    name = id_info.get("name") or email.split("@")[0].title()

    if not email:
        raise HTTPException(status_code=400, detail="Google account email is missing.")

    # Find existing user by google_id or email
    user = db.query(User).filter((User.google_id == google_id) | (User.email == email)).first()

    if user:
        if not user.google_id:
            user.google_id = google_id
            db.commit()
    else:
        # Determine authorized role
        assigned_role = determine_user_role(email, payload.target_role)

        # Check existing customer record to link
        cust = db.query(Customer).filter(Customer.email == email).first()
        if not cust and assigned_role == "CUSTOMER":
            cust = Customer(
                name=name,
                phone=f"+1-555-GOOG-{email[:4]}",
                email=email
            )
            db.add(cust)
            db.flush()

        user = User(
            email=email,
            google_id=google_id,
            hashed_password=None,  # Google OAuth account
            name=name,
            role=assigned_role,
            customer_id=cust.id if cust else None,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated.")

    access_token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.name:
        current_user.name = payload.name
    if payload.phone:
        current_user.phone = payload.phone
    if payload.address:
        current_user.address = payload.address
        if current_user.customer:
            current_user.customer.address = payload.address

    db.commit()
    db.refresh(current_user)
    return current_user

# ----------------- Manage Users (Admin Only) -----------------
@router.get("/users", response_model=List[UserOut])
def list_users(
    current_user: User = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    return db.query(User).order_by(User.id.asc()).all()

@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_role = normalize_role(payload.role)
    target_user.role = new_role
    db.commit()
    db.refresh(target_user)
    return target_user
