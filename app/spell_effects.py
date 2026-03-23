from sqlmodel import Session, select
from app.models import Hero,Monster
from fastapi import FastAPI, Depends, HTTPException
from app.database import init_db, get_session
import random
from app.utils import give_monster_rewards, hero_overflow_check


def effect_cast_fire_ball(hero ,session):
    if not hero.active_monster_id:
        return "Здесь нет врагов, чтобы пускать огненные шары!"
    
    # Ищем монстра по ID, сохраненному у героя
    monster = session.get(Monster, hero.active_monster_id)
    if not monster:
        hero.active_monster_id = None
        return "Монстр исчез в тени..."

    damage = 10 + (hero.total_intelligence * 3) + hero.level
    monster.current_hp -= int(damage)
    
    return f"Огненный шар наносит {int(damage)} урона монстру {monster.name}!"

def effect_сhain_lightning(hero ,session):
    # Ищем монстра по ID, сохраненному у героя
    monster = session.get(Monster, hero.active_monster_id)
    if not monster:
        hero.active_monster_id = None
        return "Монстр исчез в тени..."

    damage = 15 + (hero.total_intelligence * 5) + (hero.dexterity*2) + (hero.level*2)
    monster.current_hp -= int(damage)
    
    return f"Громовой разряд наносит {int(damage)} урона монстру {monster.name}!"

def effect_heal_self(hero, session):
    base_power = 5
    # Интеллект теперь реально влияет на силу магии!
    spell_power = base_power + (hero.total_intelligence *2) + hero.level

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

def effect_admin_kill(hero, session):
    if not hero.active_monster_id:
        return "Здесь нет врагов"
    
    # Ищем монстра по ID, сохраненному у героя
    monster = session.get(Monster, hero.active_monster_id)
    if not monster:
        hero.active_monster_id = None
        return "Монстр исчез в тени..."

    damage = 999999
    monster.current_hp -= int(damage)

    return f"Огненный шар наносит {int(damage)} урона монстру {monster.name}!"

def effect_fire_attack(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    # --- ХОД ГЕРОЯ ---
    hero_damage = random.randint(10+hero.total_strength+hero.intelligence, 10+ hero.total_strength + hero.total_dexterity+hero.intelligence)
    log = []

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Критический удар! Вы ударили огнянной атакой {monster.name} на {damage} урона.")
    else:
        damage = hero_damage
        log.append(f"Вы ударили огнянной атакой {monster.name} на {damage} урона.")
    
    monster.current_hp -= int(damage)

    return log

def effect_ice_attack(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    # --- ХОД ГЕРОЯ ---
    hero_damage = random.randint(10+hero.total_strength, 10+ hero.total_strength + hero.total_dexterity)
    log = []

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Критический удар! Вы ударили ледяной атакой {monster.name} двигаеться медленее. Вы наненесли {damage}.")
    else:
        damage = hero_damage
        log.append(f"Вы ударили ледяной атакой {monster.name} двигаеться медленее. Вы нанесли {damage}")
    
    monster.current_hp -= int(damage)
    hero.hp += (monster.max_attack /3)
    hero_overflow_check(hero)

    return log

def effect_crit_attack(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    # --- ХОД ГЕРОЯ ---
    hero_damage = random.randint(10+hero.total_strength, 10+ hero.total_strength + hero.total_dexterity)
    log = []
    damage = hero_damage * 2
    log.append(f"Критический удар! Вы ударили  {monster.name} на {damage} урона..")
    
    monster.current_hp -= int(damage)

    return log
    
def effect_mana_surge(hero,session):
    
    if hero.hp <= 50:
        return "Вы слишком слабы что б применить это заклинание"
    else:

        hero.hp -= 50
        hero.mp += 25

        hero_overflow_check(hero)

        return "Вы жертвуете своим здоровьем, что б востановить часть маны"

def effect_void_wrath(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    damage = hero.mp *10

    monster.current_hp -= int(damage)
    hero.mp = 0
    return f"Вы выплескиваете всю свою магическую энергию. {monster.name} получает {damage} урона! Вы полонстю опустошены..."

def effect_fire_spear(hero,session):
    monster = session.get(Monster, hero.active_monster_id)

    hero_damage = 20 + (hero.total_intelligence * 3) + hero.dexterity 
    
    log=[]

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Критический удар! Вы ударили огняным копьем {monster.name} на {damage} урона.")
    
    else:
        damage = hero_damage
        
        log.append(f"Вы ударили огняным копьем {monster.name} на {damage} урона.")
    
    monster.current_hp -= int(damage)

    return log

def effect_magic_push(hero,session):
    monster = session.get(Monster, hero.active_monster_id)

    hero_damage = 10 + (hero.total_intelligence * 2) + hero.level*3 + hero.strength 
    
    log= []

    if random.random() > 0.5:
        
        damage = hero_damage *2
        log.append(f"Вы применили магический толчек на {monster.name} он упал и получил {damage} критического урона.")
    else:
        
        damage = hero_damage
        log.append(f"Вы применили магический толчек на {monster.name} он получил {damage} урона.")

    monster.current_hp -= int(damage)
    
    return log


# Реестр: связываем строку из БД с функцией
SPELLS_EFFECTS = {
    "deal_fire_damage": effect_cast_fire_ball,
    "heal_self": effect_heal_self,
    "deal_999999_damage": effect_admin_kill,
    "fire_attack": effect_fire_attack,
    "ice_attack": effect_ice_attack,
    "crit_attack": effect_crit_attack,
    "сhain_lightning": effect_сhain_lightning,
    "mana_surge": effect_mana_surge,
    "void_wrath": effect_void_wrath,
    "fire_spear": effect_fire_spear,
    "magic_push": effect_magic_push
    
}