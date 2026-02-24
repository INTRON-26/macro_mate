from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.models import Token, User
from app.services.firebase_service import firebase_service
import os

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Routes
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    email: str = Form(..., description="User's email address"),
    username: str = Form(..., description="Unique username"),
    password: str = Form(..., description="User's password"),
    full_name: Optional[str] = Form(None, description="Optional full name")
):
    """
    Register a new user.
    
    - **email**: User's email address
    - **username**: Unique username
    - **password**: User's password (will be hashed)
    - **full_name**: Optional full name
    """
    # Check if user already exists
    existing_user = await firebase_service.get_user_by_email(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    existing_username = await firebase_service.get_user_by_username(username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    user_dict = {
        "email": email,
        "username": username,
        "full_name": full_name,
        "hashed_password": hashed_password,
        "disabled": False,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await firebase_service.create_user(email, user_dict)
    
    return User(
        email=email,
        username=username,
        full_name=full_name,
        disabled=False
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login. Use this with the Authorize button.
    
    - **username**: Your email address
    - **password**: Your password
    
    Returns an access token for authentication.
    """
    # Check if user exists (username is email)
    user = await firebase_service.get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is disabled
    if user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    email: str = Form(..., description="User's email address"),
    password: str = Form(..., description="User's password")
):
    """
    Alternative login endpoint using form fields.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns an access token that can be used for authentication.
    """
    # Check if user exists
    user = await firebase_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is disabled
    if user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from the JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await firebase_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(
        email=user["email"],
        username=user["username"],
        full_name=user.get("full_name"),
        disabled=user.get("disabled", False)
    )


@router.get("/get-info", response_model=User)
async def get_info(current_user: User = Depends(get_current_user_from_token)):
    """
    Get current authenticated user information.
    
    Requires authentication. Use the Authorize button to add your token.
    """
    return current_user
