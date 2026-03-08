import random
from app.artifacts import PRESET_ARTIFACTS
from app.encounters import PRESET_ENCOUNTERS
from app.spells import PRESET_SPELLS
from sqlmodel import Session, select
from app.models import Hero, HeroUpdate, Monster, MonsterUpdate,Artifact,HeroRead,Encounters,Spell

def give_monster_rewards(hero, monster):
    
    # Расчет золота
    gold_gain = random.randint(monster.min_gold, monster.max_gold)
    hero.gold += gold_gain
    
    # Расчет опыта 
    xp_gain = monster.xp_reward
    hero.xp += xp_gain
    
    # Очистка состояния боя
    hero.active_monster_id = None
    
    # 4. Проверка на повышение уровня 
    lvl_up_msg = ""
    if hero.xp >= 100:
        hero.level+=1
        hero.stat_points+=5
        hero.xp -= 100
        hero.hp = hero.max_hp
        hero.mp = hero.max_mp
        lvl_up_msg = f'Вы получили {hero.level} уровень !'

    return f"Победа! Получено золота: {gold_gain}, опыта: {xp_gain}.{lvl_up_msg}"

def get_room_type(floor: int, lane: int, seed: int) -> str:
    # Создаем уникальный сид для этой конкретной точки пространства
    # Чтобы комнаты на разных этажах не повторялись предсказуемо
    point_seed = f"{seed}-{floor}-{lane}"
    random.seed(point_seed)
    
    #  0 этаж всегда отдых
    if floor == 0 :
        return "R"
    #  Босс каждый 10-й этаж и этаж перед посом всегда отдых
    if floor > 0 and floor % 10 == 0:
        return "BOSS"
    if floor > 0 and floor % 9 == 0:
        return "R"
    
    # Распределение типов комнат
    # 'B' - Battle, 'S' - Shop, 'R' - Rest, 'E' - Event/Question
    roll = random.random()
    if roll < 0.6: return "B"   # 60% шанс битвы
    if roll < 0.75: return "E"  # 15% событие
    if roll < 0.90: return "S"   # 15% магазин
    return "R"                  # 10% отдых

def init_artifacts(session: Session):
    for data in PRESET_ARTIFACTS:
        # Проверяем, существует ли уже такой артефакт
        exists = session.exec(select(Artifact).where(Artifact.name == data["name"])).first()
        if not exists:
            new_art = Artifact(**data)
            session.add(new_art)
    session.commit()

def init_spells(session: Session):
    for s_data in PRESET_SPELLS:
        # Проверяем, существует ли уже спелл с таким именем
        statement = select(Spell).where(Spell.name == s_data["name"])
        existing_spell = session.exec(statement).first()
        
        if not existing_spell:
            new_spell = Spell(**s_data)
            session.add(new_spell)
    
    session.commit()

def init_encounters(session: Session):
    for data in PRESET_ENCOUNTERS:
        # Проверяем, существует ли уже такое событие
        exists = session.exec(select(Encounters).where(Encounters.name == data["name"])).first()
        if not exists:
            new_art = Encounters(**data)
            session.add(new_art)
    session.commit()


