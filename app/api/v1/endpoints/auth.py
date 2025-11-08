from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.auth import AuthService, create_tokens
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, TokenResponse

logger = structlog.get_logger()
router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if user already exists
        query = select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Create new user
        hashed_password = AuthService.get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            timezone=user_data.timezone or "UTC"
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("User registered", user_id=user.id, email=user.email)
        
        return UserResponse(
            id=user.id,
            uuid=user.uuid,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_premium=user.is_premium,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login user and return tokens"""
    try:
        # Find user by email or username
        query = select(User).where(
            (User.email == form_data.username) | (User.username == form_data.username)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not AuthService.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Create tokens
        tokens = create_tokens(user)
        
        logger.info("User logged in", user_id=user.id, email=user.email)
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
