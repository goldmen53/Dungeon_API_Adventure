# app/main.py
import random
from fastapi import FastAPI, Depends, HTTPException,Body
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
from app.routers import auth, heroes, battle, world, admin

app = FastAPI(title="Dungeon_API_Adventure")


# Подключаем модули
app.include_router(auth.router)
app.include_router(heroes.router)
app.include_router(battle.router)
app.include_router(world.router)
app.include_router(admin.router)


@app.get("/")
def read_index():
    # FastAPI просто прочитает файл index.html и отдаст его в браузер
    return FileResponse("visual.html")

# Запускаем создание таблиц при старте
@app.on_event("startup")
def on_startup():
    init_db()
    session_generator = get_session()
    session = next(session_generator)
    
    try:
        init_artifacts(session)
        init_encounters(session)
        init_spells(session)
    finally:
        session.close() # Всегда закрываем сессию вручную

@app.get("/")
def welcome():
    return {"message": "Подземелье ждет!"}

@app.get("/monsters/{name}")
def get_monster_status(name: str, session: Session = Depends(get_session)):
    # Выбрать всё из таблицы Hero, где имя совпадает
    statement = select(Monster).where(Monster.name == name)
    
    # Выполняем запрос и берем первый результат
    monster = session.exec(statement).first()
    
    # Если герой не найден 
    if not monster:
        raise HTTPException(status_code=404, detail="Монстр не найден в этом подземелье")
    
    return monster

@app.get('/monsters/')
def get_all_monsters(session: Session = Depends(get_session)):

    statement = select(Monster)

    monsters = session.exec(statement).all()

    if not monsters : 
        raise HTTPException(status_code=404, detail="В подземельни нет монстров")
    
    return monsters

@app.get("/artifacts/all")
def list_all_artifacts(session: Session = Depends(get_session)):
    artifacts = session.exec(select(Artifact)).all()
    return artifacts

@app.get("/spell/all")
def list_all_spell(session: Session = Depends(get_session)):
    spells = session.exec(select(Spell)).all()
    return spells





#---------------
#ADMIN COMMANDS
#---------------

