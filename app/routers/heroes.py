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

@router.post("/buy")
def buy_artifact( artifact_id: int, hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    artifact = session.get(Artifact, artifact_id)

    if not hero or not artifact:
        raise HTTPException(status_code=404, detail="Герой или артефакт не найден")

    current_room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)
    
    # Проверем локцию
    if current_room_type != "S":
        raise HTTPException(
            status_code=400, 
            detail=f"Артефакты можно купить только в магазине"
        )

    #  Проверяем деньги
    if hero.gold < artifact.cost:
        raise HTTPException(status_code=400, detail="Недостаточно золота!")

    # Проверяем, нет ли уже такого артефакта
    if artifact in hero.artifacts:
        raise HTTPException(status_code=400, detail="У вас уже есть этот артефакт")

    # Проверяем, есть ли этот товар именно в текущем магазине
    current_items = hero.current_shop_items.split(",") if hero.current_shop_items else []
    if str(artifact_id) not in current_items:
        raise HTTPException(status_code=400, detail="Этого товара больше нет в продаже")
    

    # Проводим сделку
    hero.gold -= artifact.cost
    hero.artifacts.append(artifact)
    
    # Удаляем купленный ID из списка магазина
    current_items.remove(str(artifact_id))
    hero.current_shop_items = ",".join(current_items)

    session.add(hero)
    session.commit()
    
    return {"message": f"Куплено: {artifact.name}", "new_gold": hero.gold}


@router.post("/pick_loot")
def pick_loot(
    choice_type: str, # "artifact" или "spell"
    choice_id: int, 
    session: Session = Depends(get_session),
    hero: Hero = Depends(get_current_hero), 

):
    # Ищем героя
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    #  Проверяем, есть ли вообще из чего выбирать
    if not hero.pending_loot:
        raise HTTPException(status_code=400, detail="У вас нет наград, ожидающих выбора")

    #  Валидация выбора: проверяем, был ли этот предмет в списке предложенных
    # pending_loot хранит список диктов: [{"type": "artifact", "id": 1, ...}, ...]
    is_valid_choice = any(
        item["type"] == choice_type and item["id"] == choice_id 
        for item in hero.pending_loot
    )
    
    if not is_valid_choice:
        raise HTTPException(status_code=400, detail="Этого предмета не было в списке ваших наград")

    #  Начисляем награду
    message = ""
    if choice_type == "artifact":
        artifact = session.get(Artifact, choice_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Артефакт не найден в базе")
        
        # Проверка на дубликаты (если артефакты уникальны)
        if artifact in hero.artifacts:
            # Если уже есть, можно дать компенсацию золотом
            hero.gold += 50
            message = f"У вас уже есть {artifact.name}. Вы получили 50 золотых вместо него."
        else:
            hero.artifacts.append(artifact)
            message = f"Вы получили артефакт: {artifact.name}!"

    elif choice_type == "spell":
        spell = session.get(Spell, choice_id)
        if not spell:
            raise HTTPException(status_code=404, detail="Заклинание не найдено")
        
        if spell in hero.spells:
            hero.gold += 30
            message = f"Вы уже знаете заклинание {spell.name}. Получено 30 золотых."
        else:
            hero.spells.append(spell)
            message = f"Вы выучили новое заклинание: {spell.name}!"
    else:
        raise HTTPException(status_code=400, detail="Неверный тип награды")

    # Очищаем список выбора, чтобы нельзя было выбрать второй раз
    hero.pending_loot = []
    
    session.add(hero)
    session.commit()
    session.refresh(hero)

    return {
        "message": message,
        "hero_id": hero.id,
        "current_artifacts": [a.name for a in hero.artifacts],
        "current_spells": [s.name for s in hero.spells]
    }   