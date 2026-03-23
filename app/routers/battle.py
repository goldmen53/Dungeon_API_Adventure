import random
from fastapi import FastAPI, Depends, HTTPException,Body,APIRouter
from app import monsters
from app.database import init_db, get_session
from app.models import Hero, HeroUpdate, Monster, MonsterUpdate,Artifact,HeroRead,Encounters,Spell,User,HighScore
from datetime import datetime
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
        raise HTTPException(status_code=400, detail="You have no active opponent")

    monster = session.get(Monster, hero.active_monster_id)
    if not monster or monster.current_hp <= 0:
        hero.active_monster_id = None
        session.add(hero)
        session.commit()
        raise HTTPException(status_code=400, detail="Opponent already defeated")

    # --- HERO TURN ---
    hero_damage = random.randint(10+hero.total_strength, 10+ hero.total_strength + hero.total_dexterity)
    log = []

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Critical hit! You hit {monster.name} for {damage} damage.")
    else:
        damage = hero_damage
        log.append(f"You hit {monster.name} for {damage} damage.")
    
    monster.current_hp -= damage

    # Artifact effects
    for art in hero.artifacts:
        handler = BATTLE_EFFECTS.get(art.effect_key)
        if handler:
            effect_msg = handler(hero, monster, damage) 
            if effect_msg: log.append(effect_msg)

    # MONSTER DEATH CHECK
    if monster.current_hp <= 0:
        reward_message = give_monster_rewards(hero, monster, session)
        session.delete(monster)
        hero.active_monster_id = None # Important to clear ID for hero
        session.add(hero)
        session.commit()
        
        log.append(f"{monster.name} killed! You received {reward_message}")
        return {"status": "victory", "log": log, "hero": hero}

    # --- MONSTER TURN ---
    if random.random() > hero.total_flee/100: 
        monster_damage = random.randint(monster.min_attack, monster.max_attack)
        hero.hp -= monster_damage
        log.append(f"{monster.name} attacks you for {monster_damage} damage.")
    else:
        log.append(f"{monster.name} missed!")

    # HERO DEATH CHECK
    if hero.hp <= 0:
        hero_name = hero.name
        user = session.get(User, hero.user_id)
        highscore = HighScore(
            username=user.username if user else "Anonymous",
            hero_name=hero.name,
            level=hero.level,
            floor=hero.current_room,
            gold=hero.gold,
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        session.add(highscore)
        session.delete(hero)
        session.commit()
        return {"status": "defeat", "log": log + ["YOU DIED..."], "hero_name": hero_name}

    # IF EVERYONE IS ALIVE — BATTLE CONTINUES
    session.add(monster)
    session.add(hero)
    session.commit()

    return {
        "status": "ongoing",
        "log": log,
        "hero_hp": f"{hero.hp}/{hero.max_hp}",
        "monster_hp": f"{monster.current_hp}/{monster.max_hp}"
    }


@router.post("/cast/{spell_id}")
def cast_spell(spell_id:int ,session: Session = Depends(get_session),hero: Hero = Depends(get_current_hero)):
    monster = session.get(Monster, hero.active_monster_id) if hero.active_monster_id else None
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    spell = session.get(Spell, spell_id)
    if not spell:
        raise HTTPException(status_code=404, detail="Spell not found")
    
    # Does hero know this spell
    if spell not in hero.spells:
         raise HTTPException(status_code=400, detail="Hero doesn't know this spell")

    # Enough mana?
    if hero.mp < spell.mp_cost:
        raise HTTPException(status_code=400, detail="Not enough mana!")
    
    log=[]


    # Artifact effects
    for art in hero.artifacts:
        handler_art = BATTLE_EFFECTS.get(art.effect_key)
        if handler_art:
            effect_msg = handler_art(hero, monster) 
            if effect_msg: log.append(effect_msg)


    handler = SPELLS_EFFECTS.get(spell.effect_key)
    if handler:
        # Spend mana before casting
        hero.mp -= spell.mp_cost
        
        # Pass session, hero, and possibly monster (if battle ongoing)
        log = [handler(hero, session)] 

    # Monster death check
    if monster.current_hp <= 0:
        reward_message = give_monster_rewards(hero, monster, session)
        session.delete(monster)
        session.commit()
        
        return {
            "status": "victory", 
            "log": log + [f"Victory! {reward_message}"], 
            "hero": hero
        }
    
    # --- MONSTER TURN IN RESPONSE ---
    if random.random() > hero.total_flee/100: 
        monster_damage = random.randint(monster.min_attack, monster.max_attack)
        hero.hp -= monster_damage
        log.append(f"{monster.name} attacks you for {monster_damage} damage.")
    else:
        log.append(f"{monster.name} missed!")

    if hero.hp <= 0:
        hero_name = hero.name
        user = session.get(User, hero.user_id)
        highscore = HighScore(
            username=user.username if user else "Anonymous",
            hero_name=hero.name,
            level=hero.level,
            floor=hero.current_room,
            gold=hero.gold,
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        session.add(highscore)
        session.delete(hero)
        session.commit()
        return {"status": "defeat", "log": log + ["You died!"], "hero_name": hero_name}

    # IF EVERYONE IS ALIVE
    session.add(monster)
    session.add(hero)
    session.commit()
    session.refresh(hero)

    # Build complete hero data for frontend
    hero_data = hero.model_dump()
    # Manually add computed properties
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
        "hero": hero_data,
        "monster_hp": f"{monster.current_hp}/{monster.max_hp}"
    }