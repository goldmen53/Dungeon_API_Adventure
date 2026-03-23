from fastapi import Depends, HTTPException,Body,APIRouter, status
from app.database import get_session
from app.models import User
from sqlmodel import Session, select
from app.auth_utils import get_password_hash,create_access_token,verify_password,validate_hero_name,validate_username,validate_password
from fastapi.security import OAuth2PasswordRequestForm



router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", status_code=201)
def register(username: str = Body(...), password: str = Body(...), session: Session = Depends(get_session)):
    # Validation
    validate_username(username)
    
    validate_password(password)

    
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this name already exists")

    new_user = User(
        username=username.lower(),
        hashed_password=get_password_hash(password)

    )
    session.add(new_user)
    session.commit()
    return {"message": "User registered successfully"}

@router.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(get_session)
):
    # 1. Find user by username
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    
    # 2. Verify existence and password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create token (put username or id in 'sub')
    access_token = create_access_token(data={"sub": user.username})
    
    # Important: FastAPI expects exactly this response format for OAuth2
    return {"access_token": access_token, "token_type": "bearer"}