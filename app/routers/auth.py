"""
Authentication & Authorization Routes (Phase 3)
Implements OAuth2 with JWT tokens, role-based access control (RBAC)
Endpoints: /auth/register, /auth/login, /auth/refresh, /auth/verify, /auth/roles
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt
import logging

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = "gericure-secret-key-phase3-production-grade-encryption-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Router
router = APIRouter(prefix="/auth", tags=["authentication"])

# ============================================================================
# MODELS & SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """User registration schema"""
    password: str
    role: str = "clinician"  # clinician, guardian, caregiver, admin


class UserInDB(UserBase):
    """User model as stored in database"""
    id: int
    hashed_password: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserResponse(UserBase):
    """User response schema (no sensitive data)"""
    id: int
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT Token payload"""
    sub: str  # username
    user_id: int
    role: str
    exp: datetime
    iat: datetime


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class RolePermission(BaseModel):
    """Role permissions schema"""
    role: str
    permissions: List[str]
    description: str


# ============================================================================
# MOCK DATABASE (Replace with real DB in production)
# ============================================================================

# In-memory user database (for demo purposes)
users_db: Dict[str, UserInDB] = {}

# Role-based permissions
ROLE_PERMISSIONS = {
    "clinician": [
        "read:patient_summary",
        "read:patient_history",
        "read:patient_alerts",
        "read:patient_medications",
        "write:alert_acknowledgment",
        "read:clinical_recommendations",
    ],
    "guardian": [
        "read:patient_summary",
        "read:patient_alerts",
        "write:patient_consent",
        "write:caregiver_observation",
        "read:caregiver_observations",
        "manage:notifications",
    ],
    "caregiver": [
        "read:patient_summary",
        "write:caregiver_observation",
        "read:caregiver_observations",
        "manage:daily_activities",
    ],
    "admin": [
        "read:patient_summary",
        "read:patient_history",
        "read:patient_alerts",
        "write:user_management",
        "read:audit_logs",
        "manage:system_config",
    ]
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, username: str, role: str, 
                       expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


def create_refresh_token(user_id: int, username: str) -> tuple[str, datetime]:
    """Create JWT refresh token (longer expiry)"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": username,
        "user_id": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Validate JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Check if user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_permission(required_permission: str):
    """Dependency to check if user has required permission"""
    async def permission_checker(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission: {required_permission}"
            )
        return current_user
    return permission_checker


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate):
    """
    Register new user
    
    - **username**: Unique username
    - **email**: Valid email address
    - **full_name**: User's full name
    - **password**: Strong password
    - **role**: clinician | guardian | caregiver | admin
    """
    # Check if user exists
    if user_data.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Validate role
    if user_data.role not in ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(ROLE_PERMISSIONS.keys())}"
        )
    
    # Hash password and create user
    hashed_pwd = hash_password(user_data.password)
    user_id = len(users_db) + 1
    
    user_in_db = UserInDB(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_pwd,
        role=user_data.role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    users_db[user_data.username] = user_in_db
    logger.info(f"User registered: {user_data.username} (role: {user_data.role})")
    
    return UserResponse(
        id=user_in_db.id,
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        role=user_in_db.role,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Login and get JWT tokens
    
    Returns both access token (30 min) and refresh token (7 days)
    """
    # Authenticate user
    user = users_db.get(credentials.username)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create tokens
    access_token, access_expires = create_access_token(
        user.id, user.username, user.role
    )
    refresh_token, _ = create_refresh_token(user.id, user.username)
    
    # Update last login
    user.last_login = datetime.utcnow()
    logger.info(f"User logged in: {user.username}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    """
    Refresh access token using refresh token
    
    Pass refresh token in request body as {"refresh_token": "..."}
    """
    try:
        body = await request.json()
        refresh_token_str = body.get("refresh_token")
    except:
        raise HTTPException(status_code=400, detail="Invalid request body")
    
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="Refresh token required")
    
    try:
        payload = jwt.decode(refresh_token_str, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = users_db.get(username)
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new access token
    access_token, access_expires = create_access_token(
        user.id, user.username, user.role
    )
    
    logger.info(f"Token refreshed for user: {username}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,  # Refresh token unchanged
        expires_in=int(ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    )


@router.get("/verify", response_model=UserResponse)
async def verify_token(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Verify current JWT token and return user info
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get("/roles", response_model=List[RolePermission])
async def get_roles():
    """
    Get all available roles and their permissions
    """
    roles = []
    role_descriptions = {
        "clinician": "Healthcare provider accessing patient records and clinical data",
        "guardian": "Legal guardian managing patient consent and receiving alerts",
        "caregiver": "Home caregiver submitting observations and daily activities",
        "admin": "System administrator with full access and system management"
    }
    
    for role, permissions in ROLE_PERMISSIONS.items():
        roles.append(RolePermission(
            role=role,
            permissions=permissions,
            description=role_descriptions.get(role, "")
        ))
    
    return roles


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Logout user (token invalidation in production)
    
    Note: In production, add token to blacklist or use token revocation list
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Successfully logged out"}


# ============================================================================
# RBAC ENFORCEMENT
# ============================================================================

class RBACMiddleware:
    """
    Middleware for role-based access control
    Can be added to FastAPI app for global authorization checks
    """
    
    @staticmethod
    def check_endpoint_access(required_role: str, current_user: UserInDB) -> bool:
        """Check if user's role meets endpoint requirements"""
        role_hierarchy = {
            "clinician": 1,
            "guardian": 1,
            "caregiver": 0,
            "admin": 999  # Admin can access everything
        }
        required_level = role_hierarchy.get(required_role, 0)
        user_level = role_hierarchy.get(current_user.role, 0)
        return user_level >= required_level


# ============================================================================
# SEED DEMO USERS
# ============================================================================

async def seed_demo_users():
    """Create demo users for testing"""
    demo_users = [
        UserCreate(
            username="dr_johnson",
            email="dr.johnson@hospital.com",
            full_name="Dr. Johnson",
            password="SecurePass123!",
            role="clinician"
        ),
        UserCreate(
            username="guardian_sarah",
            email="sarah.guardian@email.com",
            full_name="Sarah Guardian",
            password="SecurePass123!",
            role="guardian"
        ),
        UserCreate(
            username="caregiver_mary",
            email="mary.caregiver@email.com",
            full_name="Mary Caregiver",
            password="SecurePass123!",
            role="caregiver"
        ),
        UserCreate(
            username="admin_root",
            email="admin@gericure.com",
            full_name="Administrator",
            password="AdminPass123!",
            role="admin"
        ),
    ]
    
    for user_data in demo_users:
        if user_data.username not in users_db:
            hashed_pwd = hash_password(user_data.password)
            user_id = len(users_db) + 1
            
            users_db[user_data.username] = UserInDB(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_pwd,
                role=user_data.role,
                is_active=True,
                created_at=datetime.utcnow()
            )
    
    logger.info(f"Seeded {len(users_db)} demo users")
