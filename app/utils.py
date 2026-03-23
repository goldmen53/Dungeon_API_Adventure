import random
from app.artifacts import PRESET_ARTIFACTS
from app.encounters import PRESET_ENCOUNTERS
from app.spells import PRESET_SPELLS
from sqlmodel import Session, select
from app.models import Hero, HeroUpdate, Monster, MonsterUpdate,Artifact,HeroRead,Encounters,Spell

def give_monster_rewards(hero, monster,session):
    
    # Calculate gold
    gold_gain = random.randint(monster.min_gold, monster.max_gold)
    hero.gold += gold_gain
    
    # Calculate experience
    xp_gain = monster.xp_reward
    hero.xp += xp_gain
    
    # Clear battle state
    hero.active_monster_id = None

    is_boss = getattr(monster, "is_boss", False) 
    loot_drop_triggered = False
    loot_msg = ""

    if is_boss:
        loot_drop_triggered = True
    else:
        hero.fights_without_drop += 1 # Increase regular battle counter
        # 10% chance OR counter reached 10
        if random.random() <= 0.10 or hero.fights_without_drop >= 10:
            loot_drop_triggered = True
            hero.fights_without_drop = 0 # Reset counter on drop

    # GENERATE OFFERS (2 artifacts + 2 spells)
    if loot_drop_triggered:
        # Get all available artifacts and spells
        all_artifacts = session.exec(select(Artifact)).all()
        all_spells = session.exec(select(Spell)).all()

        # Select random ones (check if enough items in DB)
        sampled_arts = random.sample(all_artifacts, k=min(2, len(all_artifacts)))
        sampled_spells = random.sample(all_spells, k=min(2, len(all_spells)))

        # Write to pending_loot as list of dicts
        loot_choices = []
        for a in sampled_arts:
            loot_choices.append({"type": "artifact", "id": a.id, "name": a.name, "description": a.description})
        for s in sampled_spells:
            loot_choices.append({"type": "spell", "id": s.id, "name": s.name, "description": s.description})

        hero.pending_loot = loot_choices
        loot_msg = " Attention! You dropped rare loot. Choose one of the rewards!"
    
    # Level up check
    lvl_up_msg = ""
    while hero.xp >= 100:
        hero.level+=1
        hero.stat_points+=5
        hero.xp -= 100
        hero.hp = hero.max_hp
        hero.mp = hero.max_mp
        lvl_up_msg = f'You reached level {hero.level}!'

    return f"Victory! Gold: {gold_gain}, XP: {xp_gain}.{lvl_up_msg}{loot_msg}"

def get_room_type(floor: int, lane: int, seed: int) -> str:
    # Create unique seed for this specific point in space
    # So rooms on different floors don't repeat predictably
    point_seed = f"{seed}-{floor}-{lane}"
    random.seed(point_seed)
    
    # Boss every 10th floor
    if floor > 0 and floor % 10 == 0:
        return "BOSS"
    # Always rest before boss
    if floor > 0 and (floor % 10) % 9 == 0:
        return "R"
    
    # Room type distribution
    # 'B' - Battle, 'S' - Shop, 'R' - Rest, 'E' - Event/Question
    roll = random.random()
    if roll < 0.55: return "B"   # 50% chance battle
    if roll < 0.8: return "E"  # 25% event
    if roll < 0.9: return "S"   # 10% shop
    
    # To prevent 2 rests in a row before floor 9, replace floor 8 with battle
    else:                       
        if (floor % 10) % 8 == 0:
            return "B"
        else:
            return "R" 
    
def init_artifacts(session: Session):
    for data in PRESET_ARTIFACTS:
        # Check if artifact already exists
        exists = session.exec(select(Artifact).where(Artifact.name == data["name"])).first()
        if not exists:
            new_art = Artifact(**data)
            session.add(new_art)
    session.commit()

def init_spells(session: Session):
    for s_data in PRESET_SPELLS:
        # Check if spell with same name already exists
        statement = select(Spell).where(Spell.name == s_data["name"])
        existing_spell = session.exec(statement).first()
        
        if not existing_spell:
            new_spell = Spell(**s_data)
            session.add(new_spell)
    
    session.commit()

def init_encounters(session: Session):
    for data in PRESET_ENCOUNTERS:
        # Check if event already exists
        exists = session.exec(select(Encounters).where(Encounters.name == data["name"])).first()
        if not exists:
            new_art = Encounters(**data)
            session.add(new_art)
    session.commit()

def generate_loot_choices(session):
    # Take 2 random artifacts
    statement_arts = select(Artifact).where(Artifact.rarity != "admin")
    all_arts = session.exec(statement_spell).all()
    arts_sample = random.sample(all_arts, k=2)
    
    # Take 2 random spells

    statement_spell = select(Spell).where(Spell.rarity != "admin")
    all_spells = session.exec(statement_spell).all()
    spells_sample = random.sample(all_spells, k=2)
    
    return {
        "artifacts": arts_sample,
        "spells": spells_sample
    }

def hero_overflow_check(hero:str ,stat_max: int | None =50):
    if hero.strength > stat_max:
         hero.strength = stat_max

    if hero.agility > stat_max:
         hero.agility = stat_max

    if hero.vitality > stat_max:
         hero.vitality = stat_max

    if hero.intelligence > stat_max:
         hero.intelligence = stat_max

    if hero.dexterity > stat_max:
         hero.dexterity = stat_max 

    if hero.hp > hero.max_hp:
         hero.hp =  hero.max_hp
    
    if hero.mp > hero.max_mp:
         hero.mp = hero.max_mp

    if hero.strength < 1:
         hero.strength = 1

    if hero.agility < 1:
         hero.agility = 1

    if hero.vitality < 1:
         hero.vitality = 1

    if hero.intelligence < 1:
         hero.intelligence = 1

    if hero.dexterity < 1:
         hero.dexterity = 1 
    
    if hero.mp < 1:
         hero.mp = 1