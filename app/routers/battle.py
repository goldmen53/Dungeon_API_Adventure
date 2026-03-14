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

    # Ищем монстра
    monster = session.get(Monster, hero.active_monster_id)
    if not monster or monster.current_hp <= 0:
        # Если монстр уже мертв, но ID остался — зачищаем ID
        hero.active_monster_id = None
        session.add(hero)
        session.commit()
        raise HTTPException(status_code=400, detail="Противник уже повержен")

    # --- ХОД ГЕРОЯ ---
    # Урон героя (пока привяжем к силе strength)
    hero_damage = random.randint(hero.total_strength, hero.total_strength + 5)

    # Проверка на крит
    if random.random() <= hero.total_crit/100: 
        crit_damage = hero_damage*2
        monster.current_hp -= crit_damage
        log = [f"Критический удар! Вы ударили {monster.name} на {crit_damage} урона."]
    else:
        monster.current_hp -= hero_damage
        log = [f"Вы ударили {monster.name} на {hero_damage} урона."]

    for art in hero.artifacts:
        handler = BATTLE_EFFECTS.get(art.effect_key)
        if handler:
            # Вызываем функцию эффекта
            effect_msg = handler(hero, monster, hero_damage) 
            if effect_msg:
                log.append(effect_msg)

    # Проверка смерти монстра
    if monster.current_hp <= 0:
        reward_message = give_monster_rewards(hero, monster,session)
        # Удаляем монстра из базы, чтобы не засорять мир трупами
        session.delete(monster)
        session.add(monster)
        session.add(hero)
        session.commit()
        
        log.append(f"{monster.name} убит! Вы получили {reward_message}")
        return {"status": "victory", "log": log, "hero": hero}

    # --- ХОД МОНСТРА ---
    # Если выжил, бьет в ответ


    if random.random() > hero.total_flee/100 : # проверка на уворот 1 очко уворота = 1% 
        monster_damage = random.randint(monster.min_attack, monster.max_attack)
        hero.hp -= monster_damage
        log.append(f"{monster.name} атакует вас на {monster_damage} урона.")
    else:
        log.append(f"{monster.name} промахнулся и не нанес урон")

    # Проверка смерти героя
    if hero.hp <= 0:
        hero.hp = 0
        # Здесь потом будет логика смерти (телепортация в город или удаление)
        # 
        # ------НЕ ЗАБЫВАЕМ ДОБАВИТЬ ЛОГИКУ СМЕРТИ------
        #
        #
        log.append("Вы погибли!")
        status = "defeat"
    else:
        status = "ongoing"

    session.add(monster)
    session.add(hero)
    session.commit()

    return {
        "status": status,
        "log": log,
        "hero_hp": f"{hero.hp}/{hero.max_hp}",
        "monster_hp": f"{monster.current_hp}/{monster.max_hp}"
    }


@router.post("/cast/{spell_id}")
def cast_spell(spell_id:int ,session: Session = Depends(get_session),hero: Hero = Depends(get_current_hero)):

    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    spell = session.get(Spell, spell_id)
    if not spell:
        raise HTTPException(status_code=404, detail="Заклинание не найдено")
    
    #  знает ли герой этот спелл
    # if spell not in hero.spells:
    #     raise HTTPException(status_code=400, detail="Герой не знает этого заклинания")

    #  Хватает ли маны
    if hero.mp < spell.mp_cost:
        raise HTTPException(status_code=400, detail="Недостаточно маны!")
    
    handler = SPELLS_EFFECTS.get(spell.effect_key)
    if handler:
        # Тратим ману перед кастом
        hero.mp -= spell.mp_cost
        
        # Передаем сессию, героя и, возможно, монстра (если идет бой)
        message = handler(hero, session) 
        
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return {"message": message, "current_mp": hero.mp, "hero": hero}
    
    raise HTTPException(status_code=500, detail="У этого заклинания нет программного эффекта")
    