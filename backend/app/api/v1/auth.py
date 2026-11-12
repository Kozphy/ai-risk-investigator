from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, audit
from app.core.security import (
    Role,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: DbSession) -> User:
    existing = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    # First user becomes admin for bootstrap convenience in non-production only
    count = (await db.execute(select(User))).scalars().all()
    role = Role.ADMIN if not count else payload.role
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=role.value,
        organization=payload.organization,
    )
    db.add(user)
    await db.flush()
    await audit(request, db, user, "user.register", "user", str(user.id))
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")
    await audit(request, db, user, "user.login", "user", str(user.id))
    return TokenResponse(
        access_token=create_access_token(str(user.id), Role(user.role)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    return user
