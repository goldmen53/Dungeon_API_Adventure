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
    prefix="/admin",
    tags=["Admin Panel"]
)


@router.get("/heroes/{name}", response_model=HeroRead) 
def get_hero_status(name: str, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    return hero 

@router.get("/heroes", response_model=List[HeroRead])
def get_all_heroes(session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    heroes = session.exec(select(Hero)).all()
    
    if not heroes:
        raise HTTPException(status_code=404, detail="No heroes created yet")
    
    return heroes

@router.delete('/heroes/{name}')
def delete_hero(name:str, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    statement = select(Hero).where(Hero.name == name)
    hero = session.exec(statement).first()

    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found in this dungeon")
    #delete hero
    session.delete(hero)
    #confirm deletion
    session.commit()
    
    return {'message':f'Hero {name} has forever left the dungeon'}

@router.patch("/heroes/{name}")
def update_hero(name: str, hero_data: HeroUpdate, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    # Find hero
    db_hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    # Convert sent data to dict, excluding ones not sent (None)
    update_dict = hero_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        # Basic constraint logic (example for HP)
        if key == "hp":
            # Don't let it drop below 0 or rise above max_hp
            value = max(0, min(value, db_hero.max_hp))
        
        if key == "gold":
            # Gold cannot be negative
            value = max(0, value)

        # Apply change to object
        setattr(db_hero, key, value)

    # Save
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@router.post("/monsters/create")
def create_monster(name:str,level:int, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):

    new_monster = Monster(name=name,level=level)
    session.add(new_monster)
    session.commit()
    session.refresh(new_monster)
    return new_monster

@router.delete('admin/monsters/{name}')
def delete_monster(name:str, session:Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    statement = select(Monster).where(Monster.name == name)
    monster = session.exec(statement).first()
    if not monster:
        raise HTTPException(status_code=404, detail="Such monsters don't exist in this dungeon")
    #delete monster
    session.delete(monster)
    #confirm deletion
    session.commit()
    
    return {'message':f'Monster {name} has been forever exterminated and will no longer appear in this dungeon'}

@router.patch("/monsters/{name}")
def update_monster(name: str, monster_data: MonsterUpdate, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    
    db_monster = session.exec(select(Monster).where(Monster.name == name)).first()
    if not db_monster:
        raise HTTPException(status_code=404, detail="Monster not found")

    # Convert sent data to dict, excluding ones not sent (None)
    update_dict = monster_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        if key == "current_hp":
            # Don't let it drop below 0 or rise above max_hp
            value = max(0, min(value, db_monster.max_hp))
        

        # Apply change to object
        setattr(db_monster, key, value)

    
    session.add(db_monster)
    session.commit()
    session.refresh(db_monster)
    return db_monster

@router.post("/give_artifact")
def give_artifact(hero_name: str, artifact_id: int, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    # Find hero
    hero = session.exec(select(Hero).where(Hero.name == hero_name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    # Find artifact
    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Check: doesn't hero already have this item
    if artifact in hero.artifacts:
        raise HTTPException(status_code=400, detail="Hero already has this artifact")

    # ADD CONNECTION
    # Thanks to Relationship and LinkTable
    hero.artifacts.append(artifact)
    
    session.add(hero)
    session.commit()
    
    return {
        "message": f"Artifact '{artifact.name}' successfully given to hero {hero.name}",
        "current_artifacts": [a.name for a in hero.artifacts]
    }

@router.post("/give_spell")
def give_spell(hero_name: str, spell_id: int, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    # Find hero
    hero = session.exec(select(Hero).where(Hero.name == hero_name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    # Find spell
    spell = session.get(Spell, spell_id)
    if not spell:
        raise HTTPException(status_code=404, detail="Spell not found")

    # Check: doesn't hero already have this spell
    if spell in hero.spells:
        raise HTTPException(status_code=400, detail="Hero already knows this spell")

    # ADD CONNECTION
    # Thanks to Relationship and LinkTable
    hero.spells.append(spell)
    
    session.add(hero)
    session.commit()
    
    return {
        "message": f"Spell '{spell.name}' successfully given to hero {hero.name}",
        "current_spell": [s.name for s in hero.spells]
    }