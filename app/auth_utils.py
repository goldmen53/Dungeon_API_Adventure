from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from app.database import get_session  # Твоя функция получения сессии
from app.models import User, Hero
import bcrypt



# 1. Настройки безопасности

SECRET_KEY = "SUPER_SECRET_KEY_DONT_TELL_ANYONE" # Позже вынеси в .env
ADMIN_SECRET_TOKEN = "1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Токен живет 24 часа

# 2. Контекст для хеширования паролей
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__ident="2b" # Явно указываем современный идентификатор
)

# --- ФУНКЦИИ ДЛЯ ПАРОЛЕЙ ---

def get_password_hash(password: str) -> str:
    # Превращаем строку в байты, солим и хешируем
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

# --- ФУНКЦИИ ДЛЯ ТОКЕНОВ (JWT) ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT токен ("пропуск") для игрока"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    # Мы зашиваем ID пользователя в токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Указываем FastAPI, где искать токен (в заголовке Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить личность",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Расшифровываем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # Мы договорились класть username или id в sub
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Ищем пользователя в базе
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    
    return user

# А теперь — бонус для твоей механики "1 юзер = 1 герой"
def get_current_hero(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Hero:
    # Ищем героя, который принадлежит этому юзеру
    hero = session.exec(select(Hero).where(Hero.user_id == current_user.id)).first()
    
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="У вас еще нет созданного героя. Пожалуйста, создайте персонажа."
        )
    return hero

from fastapi import Header, HTTPException


def verify_admin(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Требуется админский доступ")
    return True