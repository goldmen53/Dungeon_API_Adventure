import random
from fastapi import FastAPI, Depends, HTTPException,Body,APIRouter, status
from app import monsters
from app.database import init_db, get_session
from app.models import Hero, HeroUpdate, Monster, MonsterUpdate,Artifact,HeroRead,Encounters,Spell,User
from sqlmodel import Session, select
from app.monsters import create_monster_params
from fastapi.responses import FileResponse
from app.effects import BATTLE_EFFECTS
from app.encounters_effects import ENCAUNTERS_EFFECTS
from app.spell_effects import SPELLS_EFFECTS
from typing import List
from app.utils import give_monster_rewards,get_room_type,init_artifacts,init_spells,init_encounters
from app.auth_utils import get_current_hero,get_password_hash,create_access_token,verify_password,get_current_user,verify_admin
from fastapi.security import OAuth2PasswordRequestForm



router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", status_code=201)
def register(
    username: str = Body(...), 
    password: str = Body(...), 
    session: Session = Depends(get_session)
):
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this name already exists")

    # Hash password and save
    new_user = User(
        username=username,
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