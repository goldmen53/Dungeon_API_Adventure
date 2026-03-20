from sqlmodel import Session, select
from app.models import Hero,Monster
from fastapi import FastAPI, Depends, HTTPException
from app.database import init_db, get_session
import random
from app.utils import give_monster_rewards


def cast_fire_damage(hero ,session):
    if not hero.active_monster_id:
        return "Здесь нет врагов, чтобы пускать огненные шары!"
    
    # Ищем монстра по ID, сохраненному у героя
    monster = session.get(Monster, hero.active_monster_id)
    if not monster:
        hero.active_monster_id = None
        return "Монстр исчез в тени..."

    damage = 10 + (hero.total_intelligence * 1.5)
    monster.current_hp -= int(damage)
    
    
    
    return f"Огненный шар наносит {int(damage)} урона монстру {monster.name}!"

def heal_self(hero, session):
    base_power = 5
    # Интеллект теперь реально влияет на силу магии!
    spell_power = base_power + hero.total_intelligence 

    if hero.hp >= hero.max_hp:
        # Возвращаем ману, если лечить нечего (опционально)
        # hero.mp += spell.mp_cost 
        return "Герой уже полностью здоров, магия рассеялась впустую."

    old_hp = hero.hp
    # Лечим, но не выше максимума
    hero.hp = min(hero.max_hp, hero.hp + spell_power)
    
    actual_healed = hero.hp - old_hp

    return (
        f"{hero.name} шепчет заклинание... Восстановлено {actual_healed} HP. "
        f"Состояние: {hero.hp}/{hero.max_hp} HP."
    )



# Реестр: связываем строку из БД с функцией
SPELLS_EFFECTS = {
    "deal_fire_damage": cast_fire_damage,
    "heal_self": heal_self
    
}