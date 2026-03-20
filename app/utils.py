import random
from app.artifacts import PRESET_ARTIFACTS
from app.encounters import PRESET_ENCOUNTERS
from app.spells import PRESET_SPELLS
from sqlmodel import Session, select
from app.models import Hero, HeroUpdate, Monster, MonsterUpdate,Artifact,HeroRead,Encounters,Spell

def give_monster_rewards(hero, monster,session):
    
    # Расчет золота
    gold_gain = random.randint(monster.min_gold, monster.max_gold)
    hero.gold += gold_gain
    
    # Расчет опыта 
    xp_gain = monster.xp_reward
    hero.xp += xp_gain
    
    # Очистка состояния боя
    hero.active_monster_id = None

    is_boss = getattr(monster, "is_boss", False) 
    loot_drop_triggered = False
    loot_msg = ""

    if is_boss:
        loot_drop_triggered = True
    else:
        hero.fights_without_drop += 1 # Увеличиваем счетчик обычных боев
        # Шанс 10% ИЛИ счетчик дошел до 10
        if random.random() <= 0.10 or hero.fights_without_drop >= 10:
            loot_drop_triggered = True
            hero.fights_without_drop = 0 # Обнуляем счетчик при выпадении

    #  ГЕНЕРАЦИЯ ПРЕДЛОЖЕНИЙ (2 арта + 2 спелла) 
    if loot_drop_triggered:
        # Получаем все доступные артефакты и заклинания
        all_artifacts = session.exec(select(Artifact)).all()
        all_spells = session.exec(select(Spell)).all()

        # Выбираем случайные (делаем проверку, чтобы в базе было достаточно вещей)
        sampled_arts = random.sample(all_artifacts, k=min(2, len(all_artifacts)))
        sampled_spells = random.sample(all_spells, k=min(2, len(all_spells)))

        # Записываем в pending_loot в формате списка словарей
        loot_choices = []
        for a in sampled_arts:
            loot_choices.append({"type": "artifact", "id": a.id, "name": a.name, "description": a.description})
        for s in sampled_spells:
            loot_choices.append({"type": "spell", "id": s.id, "name": s.name, "description": s.description})

        hero.pending_loot = loot_choices
        loot_msg = " Внимание! Вы выбили редкий лут. Выберите одну из наград!"
    
    # Проверка на повышение уровня 
    lvl_up_msg = ""
    if hero.xp >= 100:
        hero.level+=1
        hero.stat_points+=5
        hero.xp -= 100
        hero.hp = hero.max_hp
        hero.mp = hero.max_mp
        lvl_up_msg = f'Вы получили {hero.level} уровень !'

    return f"Победа! Золото: {gold_gain}, опыт: {xp_gain}.{lvl_up_msg}{loot_msg}"

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

def check_for_loot(hero, is_boss=False):
    # Если босс — дроп 100%
    if is_boss:
        return True
    
    # Инкрементируем счетчик (только для обычных мобов)
    hero.fights_without_drop += 1
    
    # Проверка на шанс 10% или Гарант (10-й бой)
    if random.random() <= 0.10 or hero.fights_without_drop >= 10:
        hero.fights_without_drop = 0  # Сбрасываем счетчик
        return True
    
    return False

def generate_loot_choices(session):
    # Берем 2 случайных артефакта
    statement_arts = select(Artifact).where(Artifact.rarity != "admin")
    all_arts = session.exec(statement_spell).all()
    arts_sample = random.sample(all_arts, k=2)
    
    # Берем 2 случайных заклинания

    statement_spell = select(Spell).where(Spell.rarity != "admin")
    all_spells = session.exec(statement_spell).all()
    spells_sample = random.sample(all_spells, k=2)
    
    return {
        "artifacts": arts_sample,
        "spells": spells_sample
    }

