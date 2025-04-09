from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import User, RefreshToken
from typing import Optional
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from .schemas import UserCreate, UserLogin, RefreshTokenRequest, TokenResponse, MessageResponse

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_data: UserCreate) -> User:
    print("Проверка email...")
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.nickname == user_data.nickname).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nickname already taken"
        )
    
    print("Хеширование пароля...")
    hashed_password = get_password_hash(user_data.password)

    print("Создание пользователя...")
    db_user = User(
        email=user_data.email,
        nickname=user_data.nickname,
        hashed_password=hashed_password
    )

    print("Добавление в БД...")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, login_data: UserLogin) -> TokenResponse:
    user = get_user_by_email(db, login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    return generate_tokens(db, user, login_data.fingerprint)

def generate_tokens(db: Session, user: User, fingerprint: str) -> TokenResponse:
    # access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    # refresh token
    refresh_token = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_refresh_token = RefreshToken(
        user_id=user.id,
        uuid=refresh_token,
        fingerprint=fingerprint,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

def refresh_tokens(db: Session, request: RefreshTokenRequest) -> TokenResponse:
    """Обновление токенов с расширенной диагностикой"""
    try:
        # 1. Логируем входящий запрос
        print(f"\n=== Refresh Request ===")
        print(f"Incoming refresh_token: {request.refresh_token}")
        print(f"Incoming fingerprint: {request.fingerprint}")

        # 2. Ищем токен в базе
        db_token = db.query(RefreshToken).filter(
            RefreshToken.uuid == request.refresh_token,
            RefreshToken.fingerprint == request.fingerprint
        ).first()

        if not db_token:
            # 3. Если токен не найден, проверяем существование в принципе
            exists = db.query(RefreshToken).filter(
                RefreshToken.uuid == request.refresh_token
            ).first()
            print(f"Token exists: {bool(exists)}")
            if exists:
                print(f"Fingerprint mismatch: DB={exists.fingerprint} != Request={request.fingerprint}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or fingerprint"
            )

        # 4. Проверяем срок действия
        current_time = datetime.now(timezone.utc)
        if db_token.expires_at < current_time:
            print(f"Token expired. Expires: {db_token.expires_at}, Current: {current_time}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )

        if db_token.revoked_at:
            print(f"Token revoked at: {db_token.revoked_at}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked"
            )

        # 5. Логируем найденный токен
        print(f"Valid token found for user: {db_token.user.email}")
        print(f"Token created: {db_token.created_at}, expires: {db_token.expires_at}")

        # 6. Удаляем старый токен
        db.delete(db_token)
        db.commit()
        print("Old token deleted successfully")

        # 7. Генерируем новые токены
        new_tokens = generate_tokens(db, db_token.user, request.fingerprint)
        print("New tokens generated successfully")
        
        return new_tokens

    except Exception as e:
        print(f"Error in refresh_tokens: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def logout_user(db: Session, token_data: RefreshTokenRequest) -> MessageResponse:
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.uuid == token_data.refresh_token,
        RefreshToken.fingerprint == token_data.fingerprint
    ).first()
    
    if refresh_token:
        db.delete(refresh_token)
        db.commit()
    
    return MessageResponse(message="Logged out successfully")