from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, Hero
import bcrypt
from fastapi import Header, HTTPException
import re


# 1. Security settings

SECRET_KEY = "SUPER_SECRET_KEY_DONT_TELL_ANYONE"
ADMIN_SECRET_TOKEN = "1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200

# 2. Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__ident="2b"
)

# --- PASSWORD FUNCTIONS ---

def get_password_hash(password: str) -> str:
    # Convert string to bytes, salt, and hash
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

# --- TOKEN (JWT) FUNCTIONS ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates JWT token ("pass") for the player"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=1440)
    
    to_encode.update({"exp": expire})
    # We embed user ID in the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Tell FastAPI where to find token (in Authorization: Bearer <token> header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Find user in database
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    
    return user


# Bonus for your "1 user = 1 hero" mechanic
def get_current_hero(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Hero:
    # Find hero in database
    hero = session.exec(select(Hero).where(Hero.user_id == current_user.id)).first()
    
    # If no hero exists
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hero not found. Create a new character."
        )
        
    return hero



def verify_admin(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return True

def validate_username(username: str):
    if len(username) < 5:
        raise HTTPException(
            status_code=400, 
            detail="Name must be longer then 5 symbols"
        )
    
    if not re.match(r"^[a-zA-Z0-9]+$", username):
        raise HTTPException(
            status_code=400, 
            detail="Account name must contain only latin letters and numbers and must be longer then 5 symbols"
        )
    

def validate_hero_name(name: str):
    
    if len(name) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Name must be longer then 3 symbols"
        )

    if not re.match(r"^[a-zA-Z0-9]+$", name):
        raise HTTPException(
            status_code=400, 
            detail="Hero name must contain only latin letters and numbers and must be longer then 3 symbols"
        )
    
def validate_password(password: str):
    
    if len(password) < 6:
        raise HTTPException(
            status_code=400, 
            detail="Password must be longer then 6 symbols"
        )
    
    
    if not re.match(r"^[\x00-\x7F]+$", password):
        raise HTTPException(
            status_code=400, 
            detail="The password can only contain Latin letters, numbers and special characters."
        )