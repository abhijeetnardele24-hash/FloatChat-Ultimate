"""Auth router (register/login/me) with JWT tokens."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import build_engine, build_session_local, get_database_url
from core.security import create_access_token, decode_access_token, hash_password, verify_password

DATABASE_URL = get_database_url()
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=128)


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_auth_tables(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                id VARCHAR(64) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.commit()


def _row_to_user(row) -> dict:
    return {
        "id": row[0],
        "email": row[1],
        "username": row[2],
        "full_name": row[3],
        "is_active": bool(row[4]),
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    ensure_auth_tables(db)
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    row = db.execute(
        text(
            """
            SELECT id, email, username, full_name, is_active
            FROM auth_users
            WHERE id = :user_id
            """
        ),
        {"user_id": user_id},
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not row[4]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account inactive")
    return _row_to_user(row)


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    ensure_auth_tables(db)

    existing = db.execute(
        text("SELECT id FROM auth_users WHERE email = :email OR username = :username"),
        {"email": payload.email.lower().strip(), "username": payload.username.strip()},
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email or username already exists")

    user_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO auth_users (id, email, username, hashed_password, full_name, is_active)
            VALUES (:id, :email, :username, :hashed_password, :full_name, TRUE)
            """
        ),
        {
            "id": user_id,
            "email": payload.email.lower().strip(),
            "username": payload.username.strip(),
            "hashed_password": hash_password(payload.password),
            "full_name": payload.full_name.strip() if payload.full_name else None,
        },
    )
    db.commit()

    user = {
        "id": user_id,
        "email": payload.email.lower().strip(),
        "username": payload.username.strip(),
        "full_name": payload.full_name.strip() if payload.full_name else None,
        "is_active": True,
    }
    token = create_access_token(subject=user_id)
    return AuthResponse(access_token=token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    ensure_auth_tables(db)
    identifier = payload.username_or_email.strip().lower()
    row = db.execute(
        text(
            """
            SELECT id, email, username, full_name, is_active, hashed_password
            FROM auth_users
            WHERE LOWER(email) = :identifier OR LOWER(username) = :identifier
            """
        ),
        {"identifier": identifier},
    ).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, row[5]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not row[4]:
        raise HTTPException(status_code=403, detail="User account inactive")

    user = _row_to_user(row)
    token = create_access_token(subject=user["id"])
    return AuthResponse(access_token=token, user=user)


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
