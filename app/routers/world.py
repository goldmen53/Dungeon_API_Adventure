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
    prefix="/world",
    tags=["World"]
)


@router.post("/rest") 
def hero_rest(hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    
    # ОПРЕДЕЛЯЕМ ТИП ТЕКУЩЕЙ ЛОКАЦИИ
    # Мы используем те же координаты и сид, что и при движении
    current_room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)
    
    #  Находимся ли мы в зоне отдыха?
    if current_room_type != "R":
        raise HTTPException(
            status_code=400, 
            detail=f"Здесь опасно! Вы не можете отдыхать в комнате типа '{current_room_type}'"
        )
    
    # ПРОВЕРКА ЗОЛОТА И ЗДОРОВЬЯ
    heal_cost = 1
    if hero.gold < heal_cost:
        raise HTTPException(status_code=400, detail="Нужно больше золота для припасов!")
    
    if hero.hp == hero.max_hp:
        return {"message": "Вы полны сил и не нуждаетесь в отдыхе."}

    # ПРИМЕНЕНИЕ ЭФФЕКТОВ
    hero.gold -= heal_cost
    hero.hp = hero.max_hp 
    
    # СОХРАНЕНИЕ
    session.add(hero)
    session.commit()
    
    return {
        "message": "Вы разбили лагерь и восстановили силы.",
        "hp": f"{hero.hp}/{hero.max_hp}",
        "gold_left": hero.gold
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
        "hero_position": {"floor": hero.current_room, "lane": hero.current_lane},
        "map_preview": visible_map
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
        # Получаем все ивенты из базы

        
        all_events = session.exec(select(Encounters)).all()

        if not all_events:
        # Если событий нет, просто идем дальше или даем золото
            hero.gold += 10
            return {"message": "Тут должно было быть событие, но мир пуст. Ты нашел 10 золотых."}

        selected_event = random.choice(all_events)
        
        # Блокируем героя этим ивентом
        hero.active_event_id = selected_event.id
        session.add(hero)
        session.commit()
        
        return {
            "type": "event",
            "event": selected_event.name,
            "message": "Вы встретили нечто странное..."
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

@router.get("/shop")
def get_shop_catalog(hero: Hero = Depends(get_current_hero),session: Session = Depends(get_session),):

    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    # Если список товаров пуст, генерируем его
    if not hero.current_shop_items:
        # Берем только те, что можно купить (base или store)
        statement = select(Artifact).where(Artifact.rarity.in_(["base", "store"]))
        all_available = session.exec(statement).all()
        
        count = min(3, len(all_available))
        selection = random.sample(all_available, k=count)
        
        # Сохраняем ID через запятую ("1,4,7")
        hero.current_shop_items = ",".join([str(a.id) for a in selection])
        session.add(hero)
        session.commit()
    
    #Получаем объекты артефактов по сохраненным ID
    item_ids = [int(i) for i in hero.current_shop_items.split(",") if i]
    if not item_ids:
        return {"hero_gold": hero.gold, "items_for_sale": [], "message": "Магазин пуст"}

    shop_items = session.exec(select(Artifact).where(Artifact.id.in_(item_ids))).all()

    return {
        "hero_gold": hero.gold,
        "items_for_sale": shop_items
    }



@router.post("/resolve_event")
def resolve_event( choice: str,hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    if not hero.active_event_id:
        raise HTTPException(status_code=400, detail="У вас нет активных событий")

    event = session.get(Encounters, hero.active_event_id)
    
    # Вызываем эффект из реестра
    handler = ENCAUNTERS_EFFECTS.get(event.effect_key)
    if handler:
        message = handler(hero, session, choice)
        session.commit()
        return {"message": message, "hero": hero}
    
    raise HTTPException(status_code=500, detail="Ошибка обработки ивента")