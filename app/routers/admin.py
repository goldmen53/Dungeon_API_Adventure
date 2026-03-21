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
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    return hero 

@router.get("/heroes", response_model=List[HeroRead])
def get_all_heroes(session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    heroes = session.exec(select(Hero)).all()
    
    if not heroes:
        raise HTTPException(status_code=404, detail="Герои еще не созданы")
    
    return heroes

@router.delete('/heroes/{name}')
def delete_hero(name:str, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    statement = select(Hero).where(Hero.name == name)
    hero = session.exec(statement).first()

    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден в этом подземелье")
    #удаляем героя
    session.delete(hero)
    #подтверждаем удаление
    session.commit()
    
    return {'message':f'Герой {name} навсегда покинул подземелье'}

@router.patch("/heroes/{name}")
def update_hero(name: str, hero_data: HeroUpdate, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    # Ищем героя
    db_hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not db_hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    # Превращаем присланные данные в словарь, исключая те, что не прислали (None)
    update_dict = hero_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        # Базовая логика ограничений (пример для HP)
        if key == "hp":
            # Не даем упасть ниже 0 и подняться выше макс_хп
            value = max(0, min(value, db_hero.max_hp))
        
        if key == "gold":
            # Золото не может быть отрицательным
            value = max(0, value)

        # Применяем изменение к объекту
        setattr(db_hero, key, value)

    # Сохраняем
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
        raise HTTPException(status_code=404, detail="Такие монстры в этом подземелье не водяться")
    #удаляем героя
    session.delete(monster)
    #подтверждаем удаление
    session.commit()
    
    return {'message':f'Монстр {name} навсегда истреблен и больше не появлеться в этом подземелии '}

@router.patch("/monsters/{name}")
def update_monster(name: str, monster_data: MonsterUpdate, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    
    db_monster = session.exec(select(Monster).where(Monster.name == name)).first()
    if not db_monster:
        raise HTTPException(status_code=404, detail="Монстр не найден")

    # Превращаем присланные данные в словарь, исключая те, что не прислали (None)
    update_dict = monster_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        if key == "current_hp":
            # Не даем упасть ниже 0 и подняться выше макс_хп
            value = max(0, min(value, db_monster.max_hp))
        

        # Применяем изменение к объекту
        setattr(db_monster, key, value)

    
    session.add(db_monster)
    session.commit()
    session.refresh(db_monster)
    return db_monster

@router.post("/give_artifact")
def give_artifact(hero_name: str, artifact_id: int, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    # Ищем героя
    hero = session.exec(select(Hero).where(Hero.name == hero_name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    # Ищем артефакт
    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Артефакт не найден")

    # Проверка: нет ли у героя уже такого предмета
    if artifact in hero.artifacts:
        raise HTTPException(status_code=400, detail="У героя уже есть этот артефакт")

    # ДОБАВЛЯЕМ СВЯЗЬ
    # Благодаря Relationship и LinkTable
    hero.artifacts.append(artifact)
    
    session.add(hero)
    session.commit()
    
    return {
        "message": f"Артефакт '{artifact.name}' успешно выдан герою {hero.name}",
        "current_artifacts": [a.name for a in hero.artifacts]
    }

@router.post("/give_spell")
def give_spell(hero_name: str, spell_id: int, session: Session = Depends(get_session),is_admin: bool = Depends(verify_admin)):
    # Ищем героя
    hero = session.exec(select(Hero).where(Hero.name == hero_name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    # Ищем артефакт
    spell = session.get(Spell, spell_id)
    if not spell:
        raise HTTPException(status_code=404, detail="Заклинание не найдено")

    # Проверка: нет ли у героя уже такого предмета
    if spell in hero.spells:
        raise HTTPException(status_code=400, detail="У героя уже есть это заклинание")

    # ДОБАВЛЯЕМ СВЯЗЬ
    # Благодаря Relationship и LinkTable
    hero.spells.append(spell)
    
    session.add(hero)
    session.commit()
    
    return {
        "message": f"Артефакт '{spell.name}' успешно выдан герою {hero.name}",
        "current_spell": [s.name for s in hero.spells]
    }   
