from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.models import User
from app.api.v1.auth.schemas import (
    UserCreate,
    UserLogin,
    RefreshTokenRequest,
    TokenResponse,
    MessageResponse,
    UserResponse
)
from .dependencies import get_current_user
from .services import (
    create_user,
    authenticate_user,
    refresh_tokens,
    logout_user
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    create_user(db, user)
    return {"message": "User registered successfully"}

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    return authenticate_user(db, user)

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)  
):
    return refresh_tokens(db, request)

@router.post("/logout", response_model=MessageResponse)
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db) 
):
    return logout_user(db, request)

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
