import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)

# database.py loads backend/.env before this value is read.
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from backend/.env")

ALGORITHM = "HS256"
ISSUER = "luna-fit-api"
AUDIENCE = "luna-fit"
TOKEN_MINUTES = 60

# Used when the email does not exist, to reduce timing differences.
DUMMY_HASH = bcrypt.hashpw(
    b"dummy-login-password",
    bcrypt.gensalt(),
)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


def unauthorized():
    return HTTPException(
        status_code=401,
        detail="Invalid credentials or expired session.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.email == str(request.email))
        .first()
    )

    password = request.password.encode("utf-8")
    stored_hash = (
        user.hashed_password.encode("utf-8")
        if user and user.hashed_password
        else DUMMY_HASH
    )

    # bcrypt passwords are limited to 72 bytes.
    if len(password) > 72:
        raise unauthorized()

    try:
        password_matches = bcrypt.checkpw(password, stored_hash)
    except ValueError:
        password_matches = False

    if not user or not password_matches or not user.is_active:
        raise unauthorized()

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "iat": now,
            "exp": now + timedelta(minutes=TOKEN_MINUTES),
            "iss": ISSUER,
            "aud": AUDIENCE,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_MINUTES * 60,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise unauthorized()

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require_exp": True,
                "require_sub": True,
            },
        )
        user_id = int(payload["sub"])
    except (JWTError, ValueError, TypeError, KeyError):
        raise unauthorized()

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user or not user.is_active:
        raise unauthorized()

    return user


@router.get("/me", response_model=schemas.UserResponse)
def current_user(user=Depends(get_current_user)):
    return user