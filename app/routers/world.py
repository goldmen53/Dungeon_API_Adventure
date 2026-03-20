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
def resolve_event(choice: str, hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    if not hero.active_event_id:
        raise HTTPException(status_code=400, detail="У вас нет активных событий")

    event = session.get(Encounters, hero.active_event_id)
    
    # 1. ЗАЩИТА ОТ ЧИТЕРОВ: Проверяем, что присланный choice реально есть в этом ивенте
    valid_choices = [
        event.choice_1_val, event.choice_2_val, event.choice_3_val, 
        event.choice_4_val, event.choice_5_val
    ]
    if choice not in valid_choices:
         raise HTTPException(status_code=400, detail="Недопустимый выбор для этого события")

    # 2. Вызываем эффект
    handler = ENCAUNTERS_EFFECTS.get(event.effect_key)
    if handler:
        message = handler(hero, session, choice)
        session.commit()
        return {"message": message, "hero": hero}
    
    raise HTTPException(status_code=500, detail="Ошибка обработки ивента: обработчик не найден")

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

@router.get("/current_event")
def get_current_event(hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    if not hero.active_event_id:
        raise HTTPException(status_code=400, detail="У вас нет активных событий")
        
    event = session.get(Encounters, hero.active_event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    # Собираем массив кнопок налету
    choices = [{"text": event.choice_1_text, "value": event.choice_1_val}]
    
    if event.choice_2_text and event.choice_2_val:
        choices.append({"text": event.choice_2_text, "value": event.choice_2_val})
    if event.choice_3_text and event.choice_3_val:
        choices.append({"text": event.choice_3_text, "value": event.choice_3_val})
    if event.choice_4_text and event.choice_4_val:
        choices.append({"text": event.choice_4_text, "value": event.choice_4_val})
    if event.choice_5_text and event.choice_5_val:
        choices.append({"text": event.choice_5_text, "value": event.choice_5_val})

    return {
        "name": event.name,
        "description": event.description,
        "choices": choices
    }