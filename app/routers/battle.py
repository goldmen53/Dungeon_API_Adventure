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
    prefix="/battle",
    tags=["Battle"]
)



@router.post("/attack")
def attack_monster(hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    if not hero or not hero.active_monster_id:
        raise HTTPException(status_code=400, detail="У вас нет активного противника")

    monster = session.get(Monster, hero.active_monster_id)
    if not monster or monster.current_hp <= 0:
        hero.active_monster_id = None
        session.add(hero)
        session.commit()
        raise HTTPException(status_code=400, detail="Противник уже повержен")

    # --- ХОД ГЕРОЯ ---
    hero_damage = random.randint(10+hero.total_strength, 10+ hero.total_strength + hero.total_dexterity)
    log = []

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Критический удар! Вы ударили {monster.name} на {damage} урона.")
    else:
        damage = hero_damage
        log.append(f"Вы ударили {monster.name} на {damage} урона.")
    
    monster.current_hp -= damage

    # Эффекты артефактов
    for art in hero.artifacts:
        handler = BATTLE_EFFECTS.get(art.effect_key)
        if handler:
            effect_msg = handler(hero, monster, damage) 
            if effect_msg: log.append(effect_msg)

    # ПРОВЕРКА СМЕРТИ МОНСТРА
    if monster.current_hp <= 0:
        reward_message = give_monster_rewards(hero, monster, session)
        session.delete(monster)
        hero.active_monster_id = None # Важно очистить ID у героя
        session.add(hero)
        session.commit()
        
        log.append(f"{monster.name} убит! Вы получили {reward_message}")
        return {"status": "victory", "log": log, "hero": hero}

    # --- ХОД МОНСТРА ---
    if random.random() > hero.total_flee/100: 
        monster_damage = random.randint(monster.min_attack, monster.max_attack)
        hero.hp -= monster_damage
        log.append(f"{monster.name} атакует вас на {monster_damage} урона.")
    else:
        log.append(f"{monster.name} промахнулся!")

    # ПРОВЕРКА СМЕРТИ ГЕРОЯ
    if hero.hp <= 0:
        hero_name = hero.name
        session.delete(hero)
        session.commit()
        return {"status": "defeat", "log": log + ["ВЫ ПОГИБЛИ..."], "hero_name": hero_name}

    # ЕСЛИ ВСЕ ЖИВЫ — БОЙ ПРОДОЛЖАЕТСЯ
    session.add(monster)
    session.add(hero)
    session.commit()

    return {
        "status": "ongoing",  # ИСПРАВЛЕНО: было "victory"
        "log": log,
        "hero_hp": f"{hero.hp}/{hero.max_hp}",
        "monster_hp": f"{monster.current_hp}/{monster.max_hp}"
    }


@router.post("/cast/{spell_id}")
def cast_spell(spell_id:int ,session: Session = Depends(get_session),hero: Hero = Depends(get_current_hero)):
    monster = session.get(Monster, hero.active_monster_id) if hero.active_monster_id else None
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    spell = session.get(Spell, spell_id)
    if not spell:
        raise HTTPException(status_code=404, detail="Заклинание не найдено")
    
    #  знает ли герой этот спелл
    if spell not in hero.spells:
         raise HTTPException(status_code=400, detail="Герой не знает этого заклинания")

    #  Хватает ли маны
    if hero.mp < spell.mp_cost:
        raise HTTPException(status_code=400, detail="Недостаточно маны!")
    
    log=[]


    # Эффекты артефактов
    for art in hero.artifacts:
        handler_art = BATTLE_EFFECTS.get(art.effect_key)
        if handler_art:
            effect_msg = handler_art(hero, monster) 
            if effect_msg: log.append(effect_msg)


    handler = SPELLS_EFFECTS.get(spell.effect_key)
    if handler:
        # Тратим ману перед кастом
        hero.mp -= spell.mp_cost
        
        # Передаем сессию, героя и, возможно, монстра (если идет бой)
        log = [handler(hero, session)] 

    # Проверка смерти монстра
    if monster.current_hp <= 0:
        reward_message = give_monster_rewards(hero, monster, session)
        session.delete(monster)
        session.commit() # Удалили и сохранили
        
        return {
            "status": "victory", 
            "log": log + [f"Победа! {reward_message}"], 
            "hero": hero
        }
    
    # --- ХОД МОНСТРА В ОТВЕТ ---
    if random.random() > hero.total_flee/100: 
        monster_damage = random.randint(monster.min_attack, monster.max_attack)
        hero.hp -= monster_damage
        log.append(f"{monster.name} атакует вас на {monster_damage} урона.")
    else:
        log.append(f"{monster.name} промахнулся!")

    if hero.hp <= 0:
        session.delete(hero)
        session.commit()
        return {"status": "defeat", "log": log + ["Вы погибли!"], "hero_name": hero.name}

    # ЕСЛИ ВСЕ ЖИВЫ
    session.add(monster)
    session.add(hero)
    session.commit()
    session.refresh(hero)

    # Формируем полные данные героя для фронтенда
    hero_data = hero.model_dump() # Получаем базовые поля
    # Добавляем вычисляемые свойства вручную
    hero_data.update({
        "max_hp": hero.max_hp,
        "total_strength": hero.total_strength,
        "total_dexterity": hero.total_dexterity,
        "total_intelligence": hero.total_intelligence,
        "total_agility": hero.total_agility,
        "total_vitality": hero.total_vitality,
        "total_flee": hero.total_flee,
        "total_crit": hero.total_crit
    })

    return {
        "status": "ongoing",
        "log": log,
        "hero": hero_data, # Отправляем расширенный объект
        "monster_hp": f"{monster.current_hp}/{monster.max_hp}"
    }
    