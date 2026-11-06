from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Customer
from app.schemas import UserRegister, UserLogin, TokenResponse, UserOut, UserProfileUpdate
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    # If registering as customer, link or create Customer record
    customer_id = None
    if payload.role == "customer":
        cust = None
        if payload.phone:
            cust = db.query(Customer).filter(Customer.phone == payload.phone).first()
        if not cust:
            cust = Customer(
                name=payload.name,
                phone=payload.phone or f"+1-555-REG-{payload.email[:4]}",
                email=payload.email.lower(),
                address=payload.address
            )
            db.add(cust)
            db.flush()
        customer_id = cust.id

    hashed = hash_password(payload.password)
    user = User(
        email=payload.email.lower(),
        hashed_password=hashed,
        name=payload.name,
        role=payload.role or "customer",
        phone=payload.phone,
        address=payload.address,
        customer_id=customer_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
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

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_profile(payload: UserProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
