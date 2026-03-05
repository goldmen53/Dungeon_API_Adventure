# app/main.py
import random
from fastapi import FastAPI, Depends, HTTPException
from app.database import init_db, get_session
from app.models import Hero, HeroUpdate, Monster, MonsterUpdate,Artifact,HeroRead
from sqlmodel import Session, select
from app.monsters import create_monster_params
from fastapi.responses import FileResponse
from app.effects import BATTLE_EFFECTS
from app.artifacts import PRESET_ARTIFACTS


app = FastAPI(title="Dungeon_API_Adventure")

def init_artifacts(session: Session):
    for data in PRESET_ARTIFACTS:
        # Проверяем, существует ли уже такой артефакт
        exists = session.exec(select(Artifact).where(Artifact.name == data["name"])).first()
        if not exists:
            new_art = Artifact(**data)
            session.add(new_art)
    session.commit()

@app.get("/")
def read_index():
    # FastAPI просто прочитает файл index.html и отдаст его в браузер
    return FileResponse("index.html")

# Запускаем создание таблиц при старте
@app.on_event("startup")
def on_startup():
    init_db()
    session_generator = get_session()
    session = next(session_generator)
    
    try:
        init_artifacts(session)
    finally:
        session.close() # Всегда закрываем сессию вручную


@app.get("/")
def welcome():
    return {"message": "Подземелье ждет!"}


@app.post("/heroes/create")
def create_hero(name: str, session: Session = Depends(get_session)):
    # Проверяем, нет ли уже такого имени
    existing = session.exec(select(Hero).where(Hero.name == name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Это имя уже занято")

    # Создаем героя. world_seed сгенерируется сам благодаря Field(default_factory)
    new_hero = Hero(name=name)
    
    session.add(new_hero)
    session.commit()
    session.refresh(new_hero)
    
    return {
        "message": f"Герой {new_hero.name} вошел в подземелье!",
        "hero_id": new_hero.id,
        "world_seed": new_hero.world_seed,
        "start_position": f"Floor: {new_hero.current_room}, Lane: {new_hero.current_lane}"
    }

@app.get("/heroes/{name}", response_model=HeroRead) 
def get_hero_status(name: str, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    return hero 
from typing import List

@app.get("/heroes/", response_model=List[HeroRead])
def get_all_heroes(session: Session = Depends(get_session)):
    heroes = session.exec(select(Hero)).all()
    
    if not heroes:
        raise HTTPException(status_code=404, detail="Герои еще не созданы")
    
    return heroes

@app.delete('/heroes/{name}')
def delete_hero(name:str, session: Session = Depends(get_session)):
    statement = select(Hero).where(Hero.name == name)
    hero = session.exec(statement).first()

    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден в этом подземелье")
    #удаляем героя
    session.delete(hero)
    #подтверждаем удаление
    session.commit()
    
    return {'message':f'Герой {name} навсегда покинул подземелье'}

@app.patch("/heroes/{name}")
def update_hero(name: str, hero_data: HeroUpdate, session: Session = Depends(get_session)):
    # Ищем героя
    db_hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not db_hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    # Превращаем присланные данные в словарь, исключая те, что не прислали (None)
    update_dict = hero_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        # Базовая логика ограничений (пример для HP)
        if key == "current_hp":
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

@app.post("/heroes/{name}/rest")  # Переименуем для атмосферности
def hero_rest(name: str, session: Session = Depends(get_session)):
    # Загружаем героя из базы
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    # ОПРЕДЕЛЯЕМ ТИП ТЕКУЩЕЙ ЛОКАЦИИ
    # Мы используем те же координаты и сид, что и при движении
    current_room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)
    
    #  Находимся ли мы в зоне отдыха?
    if current_room_type != "R":
        raise HTTPException(
            status_code=400, 
            detail=f"Здесь опасно! Вы не можете отдыхать в комнате типа '{current_room_type}'"
        )
    
    # ПРОВЕРКА ЗОЛОТА И ЗДОРОВЬЯ
    heal_cost = 10
    if hero.gold < heal_cost:
        raise HTTPException(status_code=400, detail="Нужно больше золота для припасов!")
    
    if hero.hp == hero.max_hp:
        return {"message": "Вы полны сил и не нуждаетесь в отдыхе."}

    # ПРИМЕНЕНИЕ ЭФФЕКТОВ
    hero.gold -= heal_cost
    hero.hp = hero.max_hp 
    
    # СОХРАНЕНИЕ
    session.add(hero)
    session.commit()
    
    return {
        "message": "Вы разбили лагерь и восстановили силы.",
        "hp": f"{hero.hp}/{hero.max_hp}",
        "gold_left": hero.gold
    }

@app.post("/heroes/{name}/spell/heal")
def spell_heal(name: str, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    base_power= 5
    spell_power= base_power + hero.intelligence

    mp_cost = 1
    if hero.mp < mp_cost:
        return {"message": "Недостаточно МP"}
    if hero.hp == hero.max_hp:
        return {"message": "Герой уже полностью здоров"}
    
    hero.mp -= mp_cost

    if hero.hp + spell_power > hero.max_hp:
        hero.hp = hero.max_hp
        
    else : hero.hp+=spell_power

    session.add(hero)
    session.commit()
    session.refresh(hero)

    return {
        "message": (
            f" {hero.name} шепчет заклинание... Восстановлено {spell_power} HP. "
            f"Текущее состояние: {hero.hp}/{hero.max_hp} HP, {hero.mp}/{hero.max_mp} MP."
        )
    }

@app.post("/monsters/create")
def create_monster(name:str,level:int, session: Session = Depends(get_session)):

    new_monster = Monster(name=name,level=level)
    session.add(new_monster)
    session.commit()
    session.refresh(new_monster)
    return new_monster

@app.get("/monsters/{name}")
def get_monster_status(name: str, session: Session = Depends(get_session)):
    # Выбрать всё из таблицы Hero, где имя совпадает
    statement = select(Monster).where(Monster.name == name)
    
    # Выполняем запрос и берем первый результат
    monster = session.exec(statement).first()
    
    # Если герой не найден 
    if not monster:
        raise HTTPException(status_code=404, detail="Монстр не найден в этом подземелье")
    
    return monster

@app.delete('/monsters/{name}')
def delete_monster(name:str, session:Session = Depends(get_session)):
    statement = select(Monster).where(Monster.name == name)
    monster = session.exec(statement).first()
    if not monster:
        raise HTTPException(status_code=404, detail="Такие монстры в этом подземелье не водяться")
    #удаляем героя
    session.delete(monster)
    #подтверждаем удаление
    session.commit()
    
    return {'message':f'Монстр {name} навсегда истреблен и больше не появлеться в этом подземелии '}

@app.patch("/monsters/{name}")
def update_monster(name: str, monster_data: MonsterUpdate, session: Session = Depends(get_session)):
    
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

@app.get('/monsters/')
def get_all_monsters(session: Session = Depends(get_session)):

    statement = select(Monster)

    monsters = session.exec(statement).all()

    if not monsters : 
        raise HTTPException(status_code=404, detail="В подземельни нет монстров")
    
    return monsters

    
@app.get("/heroes/{name}/map")
def get_hero_map(name: str, session: Session = Depends(get_session)):   
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    visible_map = []
    # Показываем текущий этаж 
    if hero.current_room < 11:
        map = 0
    else:
        map = (hero.current_room //10 )*10
    #уникальный спагети код для отрисовки 0 этажа возможно потом убрать 
    if hero.current_room < 11:
        for f in range( map,map+11 ):
            floor_data = {
                "floor": f"F{f}",
                "lanes": {
                    "Left (0)": get_room_type(f, 0, hero.world_seed),
                    "Center (1)": get_room_type(f, 1, hero.world_seed),
                    "Right (2)": get_room_type(f, 2, hero.world_seed)
                },
                "is_current": f == hero.current_room
            }
            visible_map.append(floor_data)

    else:
        for f in range( map+1,map+11 ):
            floor_data = {
                "floor": f"F{f}",
                "lanes": {
                    "Left (0)": get_room_type(f, 0, hero.world_seed),
                    "Center (1)": get_room_type(f, 1, hero.world_seed),
                    "Right (2)": get_room_type(f, 2, hero.world_seed)
                },
                "is_current": f == hero.current_room
            }
            visible_map.append(floor_data)
        
    return {
        "hero_position": {"floor": hero.current_room, "lane": hero.current_lane},
        "map_preview": visible_map
    }


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



@app.post("/heroes/{name}/move")
def move_hero(name: str, target_lane: int, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    # Сначала ПРОВЕРКА БОЯ (нельзя уйти из текущей комнаты, если там враг)
    if hero.active_monster_id:
        monster = session.get(Monster, hero.active_monster_id)
        if monster and monster.current_hp > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Вы не можете уйти, пока жив {monster.name}!"
            )

    # ПРОВЕРКА ДОРОЖКИ (можно только на соседние)
    allowed_lanes = [hero.current_lane, hero.current_lane - 1, hero.current_lane + 1]
    if target_lane not in allowed_lanes or target_lane not in [0, 1, 2]:
         raise HTTPException(status_code=400, detail="Недопустимый переход")

    #  ШАГ ВПЕРЕД (Меняем координаты ПЕРЕД генерацией типа комнаты)
    hero.current_room += 1
    hero.current_lane = target_lane
    
    # ОПРЕДЕЛЯЕМ ТИП НОВОЙ КОМНАТЫ
    room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)

    # ЛОГИКА СПАВНА
    m_params = None
    if room_type == "B" or room_type == "BOSS":
        m_params = create_monster_params(hero.current_room, is_boss=(room_type == "BOSS"))
        new_monster = Monster(**m_params)
        session.add(new_monster)
        session.flush() 
        hero.active_monster_id = new_monster.id
    else:
        hero.active_monster_id = None

    #логика обовления магазина. При каждом шаге сбрасывем магазин и генерируем заново
    hero.current_shop_items = None

    session.add(hero)
    session.commit()
    session.refresh(hero)
    
    return {
        "event": "Вы встретили врага!" if hero.active_monster_id else "Вы вошли в мирную зону",
        "current_floor": hero.current_room,
        "room_type": room_type,
        "monster": m_params
    }

@app.post("/battle/attack")
def attack_monster(hero_name: str, session: Session = Depends(get_session)):
    # Ищем героя
    hero = session.exec(select(Hero).where(Hero.name == hero_name)).first()
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
        monster.current_hp = 0
        
        
        # Выдаем награду
        gold_gain = random.randint(monster.min_gold, monster.max_gold)
        hero.gold += gold_gain
        hero.xp += monster.xp_reward
        hero.active_monster_id = None # Путь свободен

        if hero.xp >= 100:
            hero.level+=1
            hero.stat_points+=5
            hero.xp -= 100
            hero.hp = hero.max_hp
            hero.mp = hero.max_mp
            log.append(f'Вы получили {hero.level} уровень !')
        session.add(monster)
        session.add(hero)
        session.commit()
        
        log.append(f"{monster.name} убит! Вы получили {gold_gain} золота и {monster.xp_reward} опыта.")
        return {"status": "victory", "log": log, "hero": hero}

    # --- ХОД МОНСТРА ---
    # Если выжил, бьет в ответ
    monster_damage = random.randint(monster.min_attack, monster.max_attack)
    hero.hp -= monster_damage
    log.append(f"{monster.name} атакует вас на {monster_damage} урона.")

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

@app.post("/heroes/{name}/upgrade")
def upgrade_stat(name: str, stat: str,amount: int, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
    
    if hero.stat_points <= 0:
        raise HTTPException(status_code=400, detail="У вас нет свободных очков характеристик")
    
    if amount > hero.stat_points:
        raise HTTPException(status_code=400, detail="У вас недостаточно очков характеристик")
    
    
    if stat == "str":
        hero.strength += amount
    elif stat == "agi":
        hero.agility += amount
    
    elif stat == "vit":
        hero.vitality += amount
        # Сразу обновляем макс ХП по  формуле 
        hero.hp += (hero.vitality*10)
    
    elif stat == "int":
        hero.intelligence += amount
    elif stat == "dex":
        hero.dexterity += amount

    else:
        raise HTTPException(status_code=400, detail="Неверная характеристика")
    
    hero.stat_points -= amount

    session.add(hero)
    session.commit()
    session.refresh(hero)
    
    return {
        "message": f"{stat} успешно увеличена!",
        "current_stats": {
            "str": hero.strength,
            "agi": hero.agility,
            "vit": hero.vitality,
            "int": hero.intelligence,
            "dex": hero.dexterity,
            "points_left": hero.stat_points
        }
    }

@app.post("/admin/give_artifact")
def give_artifact(hero_name: str, artifact_id: int, session: Session = Depends(get_session)):
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


@app.get("/artifacts/all")
def list_all_artifacts(session: Session = Depends(get_session)):
    artifacts = session.exec(select(Artifact)).all()
    return artifacts

@app.get("/heroes/{name}/shop")
def get_shop_catalog(name: str, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    # Если список товаров пуст, генерируем его
    if not hero.current_shop_items:
        # Берем только те, что можно купить (base или store)
        statement = select(Artifact).where(Artifact.rarity.in_(["base", "store"]))
        all_available = session.exec(statement).all()
        
        count = min(3, len(all_available))
        selection = random.sample(all_available, k=count)
        
        # Сохраняем ID через запятую ("1,4,7")
        hero.current_shop_items = ",".join([str(a.id) for a in selection])
        session.add(hero)
        session.commit()
    
    #Получаем объекты артефактов по сохраненным ID
    item_ids = [int(i) for i in hero.current_shop_items.split(",") if i]
    if not item_ids:
        return {"hero_gold": hero.gold, "items_for_sale": [], "message": "Магазин пуст"}

    shop_items = session.exec(select(Artifact).where(Artifact.id.in_(item_ids))).all()

    return {
        "hero_gold": hero.gold,
        "items_for_sale": shop_items
    }

@app.post("/heroes/{name}/buy")
def buy_artifact(name: str, artifact_id: int, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    artifact = session.get(Artifact, artifact_id)

    if not hero or not artifact:
        raise HTTPException(status_code=404, detail="Герой или артефакт не найден")

    current_room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)
    
    # Проверем локцию
    if current_room_type != "S":
        raise HTTPException(
            status_code=400, 
            detail=f"Артефакты можно купить только в магазине"
        )

    #  Проверяем деньги
    if hero.gold < artifact.cost:
        raise HTTPException(status_code=400, detail="Недостаточно золота!")

    # Проверяем, нет ли уже такого артефакта
    if artifact in hero.artifacts:
        raise HTTPException(status_code=400, detail="У вас уже есть этот артефакт")

    # Проверяем, есть ли этот товар именно в текущем магазине
    current_items = hero.current_shop_items.split(",") if hero.current_shop_items else []
    if str(artifact_id) not in current_items:
        raise HTTPException(status_code=400, detail="Этого товара больше нет в продаже")
    

    # Проводим сделку
    hero.gold -= artifact.cost
    hero.artifacts.append(artifact)
    
    # Удаляем купленный ID из списка магазина
    current_items.remove(str(artifact_id))
    hero.current_shop_items = ",".join(current_items)

    session.add(hero)
    session.commit()
    
    return {"message": f"Куплено: {artifact.name}", "new_gold": hero.gold}

