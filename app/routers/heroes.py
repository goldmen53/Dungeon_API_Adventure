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
    current_user: User = Depends(get_current_user) # Получаем юзера из токена
):
    # Проверяем, нет ли уже такого имени
    existing_name = session.exec(select(Hero).where(Hero.name == name)).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Это имя уже занято")

    # Проверяем, нет ли уже героя у этого аккаунта 
    existing_hero = session.exec(select(Hero).where(Hero.user_id == current_user.id)).first()
    if existing_hero:
        raise HTTPException(status_code=400, detail="У вас уже есть активный герой")

    # Создаем героя, привязывая его к ID текущего юзера
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
    if not hero:
        return None
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

@router.post("/move")
def move_hero(target_lane: int,hero: Hero = Depends(get_current_hero),session: Session = Depends(get_session)):

    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    # Сначала ПРОВЕРКА БОЯ (нельзя уйти из текущей комнаты, если там враг)
    if hero.active_monster_id:
        monster = session.get(Monster, hero.active_monster_id)
        if monster and monster.current_hp > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Вы не можете уйти, пока жив {monster.name}!"
            )

    # ПРОВЕРКА ДОРОЖКИ (можно только на соседние)
    allowed_lanes = [hero.current_lane, hero.current_lane - 1, hero.current_lane + 1]
    if target_lane not in allowed_lanes or target_lane not in [0, 1, 2]:
         raise HTTPException(status_code=400, detail="Недопустимый переход")

    #  ШАГ ВПЕРЕД (Меняем координаты ПЕРЕД генерацией типа комнаты)
    hero.current_room += 1
    hero.current_lane = target_lane
    
    # ОПРЕДЕЛЯЕМ ТИП НОВОЙ КОМНАТЫ
    room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)

    # ЛОГИКА СПАВНА
    m_params = None
    if room_type == "B" or room_type == "BOSS":
        m_params = create_monster_params(hero.current_room, is_boss=(room_type == "BOSS"))
        new_monster = Monster(**m_params)
        session.add(new_monster)
        session.flush() 
        hero.active_monster_id = new_monster.id
    else:
        hero.active_monster_id = None

    if room_type == "E":
        all_events = session.exec(select(Encounters)).all()
        if not all_events:
            hero.gold += 10
            return {"message": "Тут должно было быть событие, но мир пуст. Ты нашел 10 золотых."}

        selected_event = random.choice(all_events)
        
        # Блокируем героя
        hero.active_event_id = selected_event.id
        session.add(hero)
        session.commit()
        
        # --- ФОРМИРУЕМ МАССИВ КНОПОК ДЛЯ ФРОНТЕНДА ---
        choices = []
        # Вариант 1 всегда есть
        choices.append({"text": selected_event.choice_1_text, "value": selected_event.choice_1_val})
        
        # Проверяем опциональные
        if selected_event.choice_2_text and selected_event.choice_2_val:
            choices.append({"text": selected_event.choice_2_text, "value": selected_event.choice_2_val})
        if selected_event.choice_3_text and selected_event.choice_3_val:
            choices.append({"text": selected_event.choice_3_text, "value": selected_event.choice_3_val})
        if selected_event.choice_4_text and selected_event.choice_4_val:
            choices.append({"text": selected_event.choice_4_text, "value": selected_event.choice_4_val})
        if selected_event.choice_5_text and selected_event.choice_5_val:
            choices.append({"text": selected_event.choice_5_text, "value": selected_event.choice_5_val})

        return {
            "type": "event",
            "event_name": selected_event.name,
            "description": selected_event.description,
            "choices": choices  # Отдаем готовый массив вариантов!
        }


    #логика обовления магазина. При каждом шаге сбрасывем магазин и генерируем заново
    hero.current_shop_items = None

    session.add(hero)
    session.commit()
    session.refresh(hero)
    
    return {
        "event": "Вы встретили врага!" if hero.active_monster_id else "Вы вошли в мирную зону",
        "current_floor": hero.current_room,
        "room_type": room_type,
        "monster": m_params
    }

@router.get("/map")
def get_hero_map(hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):   
    
    visible_map = []
    # Показываем текущий этаж 
    if hero.current_room < 11:
        map = 0
    else:
        map = (hero.current_room //10 )*10
    #уникальный спагети код для отрисовки 0 этажа возможно потом убрать 
    if hero.current_room < 11:
        for f in range( map,map+11 ):
            floor_data = {
                "floor": f"F{f}",
                "lanes": {
                    "Left (0)": get_room_type(f, 0, hero.world_seed),
                    "Center (1)": get_room_type(f, 1, hero.world_seed),
                    "Right (2)": get_room_type(f, 2, hero.world_seed)
                },
                "is_current": f == hero.current_room
            }
            visible_map.append(floor_data)

    else:
        for f in range( map+1,map+11 ):
            floor_data = {
                "floor": f"F{f}",
                "lanes": {
                    "Left (0)": get_room_type(f, 0, hero.world_seed),
                    "Center (1)": get_room_type(f, 1, hero.world_seed),
                    "Right (2)": get_room_type(f, 2, hero.world_seed)
                },
                "is_current": f == hero.current_room
            }
            visible_map.append(floor_data)
        
    return {
    "hero_position": {
        "floor": hero.current_room, 
        "lane": hero.current_lane,
        "room_type": get_room_type(hero.current_room, hero.current_lane, hero.world_seed),
        "is_rest_zone": get_room_type(hero.current_room, hero.current_lane, hero.world_seed) == "R"
    },
    "map_preview": visible_map
}