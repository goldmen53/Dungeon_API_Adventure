from sqlmodel import Session, select
from app.models import Hero,Monster
from fastapi import FastAPI, Depends, HTTPException
from app.database import init_db, get_session
import random
from app.utils import give_monster_rewards, hero_overflow_check


def effect_cast_fire_ball(hero ,session):
    if not hero.active_monster_id:
        return "There are no enemies here to cast fireballs at!"
    
    # Find monster by ID saved in hero
    monster = session.get(Monster, hero.active_monster_id)
    if not monster:
        hero.active_monster_id = None
        return "Monster vanished into shadow..."

    damage = 10 + (hero.total_intelligence * 3) + hero.level
    monster.current_hp -= int(damage)
    
    return f"Fireball deals {int(damage)} damage to monster {monster.name}!"

def effect_сhain_lightning(hero ,session):
    # Find monster by ID saved in hero
    monster = session.get(Monster, hero.active_monster_id)
    if not monster:
        hero.active_monster_id = None
        return "Monster vanished into shadow..."

    damage = 15 + (hero.total_intelligence * 5) + (hero.dexterity*2) + (hero.level*2)
    monster.current_hp -= int(damage)
    
    return f"Thunder bolt deals {int(damage)} damage to monster {monster.name}!"

def effect_heal_self(hero, session):
    base_power = 5
    # Intelligence now actually affects magic power!
    spell_power = base_power + (hero.total_intelligence *2) + hero.level

    if hero.hp >= hero.max_hp:
        # Return mana if nothing to heal (optional)
        # hero.mp += spell.mp_cost 
        return "Hero is already fully healthy, magic dissipated for nothing."

    old_hp = hero.hp
    # Heal but not above maximum
    hero.hp = min(hero.max_hp, hero.hp + spell_power)
    
    actual_healed = hero.hp - old_hp

    return (
        f"{hero.name} whispers the spell... Restored {actual_healed} HP. "
        f"Status: {hero.hp}/{hero.max_hp} HP."
    )

def effect_admin_kill(hero, session):
    if not hero.active_monster_id:
        return "There are no enemies here"
    
    # Find monster by ID saved in hero
    monster = session.get(Monster, hero.active_monster_id)
    if not monster:
        hero.active_monster_id = None
        return "Monster vanished into shadow..."

    damage = 999999
    monster.current_hp -= int(damage)

    return f"Fireball deals {int(damage)} damage to monster {monster.name}!"

def effect_fire_attack(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    # --- HERO TURN ---
    hero_damage = random.randint(10+hero.total_strength+hero.intelligence, 10+ hero.total_strength + hero.total_dexterity+hero.intelligence)
    log = []

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Critical hit! You hit with fire attack {monster.name} for {damage} damage.")
    else:
        damage = hero_damage
        log.append(f"You hit with fire attack {monster.name} for {damage} damage.")
    
    monster.current_hp -= int(damage)

    return log

def effect_ice_attack(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    # --- HERO TURN ---
    hero_damage = random.randint(10+hero.total_strength, 10+ hero.total_strength + hero.total_dexterity)
    log = []

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Critical hit! You hit with ice attack {monster.name} it moves slower. You dealt {damage}.")
    else:
        damage = hero_damage
        log.append(f"You hit with ice attack {monster.name} it moves slower. You dealt {damage}")
    
    monster.current_hp -= int(damage)
    hero.hp += (monster.max_attack /3)
    hero_overflow_check(hero)

    return log

def effect_crit_attack(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    # --- HERO TURN ---
    hero_damage = random.randint(10+hero.total_strength, 10+ hero.total_strength + hero.total_dexterity)
    log = []
    damage = hero_damage * 2
    log.append(f"Critical hit! You hit {monster.name} for {damage} damage..")
    
    monster.current_hp -= int(damage)

    return log
    
def effect_mana_surge(hero,session):
    
    if hero.hp <= 50:
        return "You are too weak to cast this spell"
    else:

        hero.hp -= 50
        hero.mp += 25

        hero_overflow_check(hero)

        return "You sacrifice your health to restore some mana"

def effect_void_wrath(hero,session):
    monster = session.get(Monster, hero.active_monster_id)
    damage = hero.mp *10

    monster.current_hp -= int(damage)
    hero.mp = 0
    return f"You unleash all your magical energy. {monster.name} takes {damage} damage! You are completely depleted..."

def effect_fire_spear(hero,session):
    monster = session.get(Monster, hero.active_monster_id)

    hero_damage = 20 + (hero.total_intelligence * 3) + hero.dexterity 
    
    log=[]

    if random.random() <= hero.total_crit/100: 
        damage = hero_damage * 2
        log.append(f"Critical hit! You hit with fire spear {monster.name} for {damage} damage.")
    
    else:
        damage = hero_damage
        
        log.append(f"You hit with fire spear {monster.name} for {damage} damage.")
    
    monster.current_hp -= int(damage)

    return log

def effect_magic_push(hero,session):
    monster = session.get(Monster, hero.active_monster_id)

    hero_damage = 10 + (hero.total_intelligence * 2) + hero.level*3 + hero.strength 
    
    log=[]

    if random.random() > 0.5:
        
        damage = hero_damage *2
        log.append(f"You used magic push on {monster.name} it fell and took {damage} critical damage.")
    else:
        
        damage = hero_damage
        log.append(f"You used magic push on {monster.name} it took {damage} damage.")

    monster.current_hp -= int(damage)
    
    return log


# Registry: link string from DB with function
SPELLS_EFFECTS = {
    "deal_fire_damage": effect_cast_fire_ball,
    "heal_self": effect_heal_self,
    "deal_999999_damage": effect_admin_kill,
    "fire_attack": effect_fire_attack,
    "ice_attack": effect_ice_attack,
    "crit_attack": effect_crit_attack,
    "сhain-lightning": effect_сhain_lightning,
    "mana_surge": effect_mana_surge,
    "void_wrath": effect_void_wrath,
    "fire_spear": effect_fire_spear,
    "magic_push": effect_magic_push
    
}