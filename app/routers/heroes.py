import random
from fastapi import FastAPI, Depends, HTTPException,Body,APIRouter
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
    prefix="/heroes",
    tags=["Heroes"] # Группировка в Swagger
)

@router.post("/create")
def create_hero(
    name: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # 1. Получаем юзера из токена
):
    # 2. Проверяем, нет ли уже такого имени (твой код)
    existing_name = session.exec(select(Hero).where(Hero.name == name)).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Это имя уже занято")

    # 3. Проверяем, нет ли уже героя у этого аккаунта (Roguelike правило: 1 юзер = 1 герой)
    existing_hero = session.exec(select(Hero).where(Hero.user_id == current_user.id)).first()
    if existing_hero:
        raise HTTPException(status_code=400, detail="У вас уже есть активный герой")

    # 4. Создаем героя, привязывая его к ID текущего юзера
    new_hero = Hero(name=name, user_id=current_user.id)
    
    session.add(new_hero)
    session.commit()
    session.refresh(new_hero)
    
    return {
        "message": f"Герой {new_hero.name} вошел в подземелье!",
        "hero_id": new_hero.id,
        "world_seed": new_hero.world_seed,
        "start_position": f"Floor: {new_hero.current_room}, Lane: {new_hero.current_lane}"
    }


@router.get("/me", response_model=HeroRead)
def get_my_hero(hero: Hero = Depends(get_current_hero)):
    # Если герой есть, get_current_hero его вернет. 
    # Если его нет (умер или не создан), вылетит 404 — и фронтенд поймет, что делать.
    return hero

@router.post("/upgrade")
def upgrade_stat(stat: str,amount: int,hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    if hero.stat_points <= 0:
        raise HTTPException(status_code=400, detail="У вас нет свободных очков характеристик")
    
    if amount > hero.stat_points:
        raise HTTPException(status_code=400, detail="У вас недостаточно очков характеристик")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="К-во не может быть отрицательным или равным нулю")
    

    if stat == "str" and (amount + hero.strength) <=50:
        hero.strength += amount
    elif stat == "agi" and (amount + hero.agility) <=50:
        hero.agility += amount
    
    elif stat == "vit" and (amount + hero.vitality) <=50:
        hero.vitality += amount
        # Сразу обновляем макс ХП по  формуле 
        hero.hp += (hero.vitality*10)
        if hero.hp > hero.max_hp:
            hero.hp = hero.max_hp

    elif stat == "int" and (amount + hero.intelligence) <=50:
        hero.intelligence += amount
    elif stat == "dex" and (amount + hero.dexterity) <=50:
        hero.dexterity += amount

    else:
        raise HTTPException(status_code=400, detail="Неверная характеристика или характеристика >50")
    
    hero.stat_points -= amount

    session.add(hero)
    session.commit()
    session.refresh(hero)
    
    return {
        "message": f"{stat} успешно увеличена!",
        "current_stats": {
            "str": hero.strength,
            "agi": hero.agility,
            "vit": hero.vitality,
            "int": hero.intelligence,
            "dex": hero.dexterity,
            "points_left": hero.stat_points
        }
    }

