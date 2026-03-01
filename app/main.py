# app/main.py
import random
from fastapi import FastAPI, Depends, HTTPException
from app.database import init_db, get_session
from app.models import Hero, HeroUpdate, Monster, MonsterUpdate
from sqlmodel import Session, select 

app = FastAPI(title="Dungeon_API_Adventure")

# Запускаем создание таблиц при старте
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def welcome():
    return {"message": "Подземелье ждет!"}

# Эндпоинт для создания героя
@app.post("/heroes/create")
def create_hero(name: str, char_class: str, session: Session = Depends(get_session)):
    # Логика начальных статов
    stats = {"strength": 10, "vitality": 10, "intelligence": 10}
    
    if char_class == "warrior":
        stats["strength"] += 5
        stats["vitality"] += 5
    elif char_class == "mage":
        stats["intelligence"] += 10
        stats["vitality"] -= 2

    new_hero = Hero(name=name, hero_class=char_class, **stats)
    
    session.add(new_hero)
    session.commit()
    session.refresh(new_hero)
    return new_hero

@app.get("/heroes/{name}")
def get_hero_status(name: str, session: Session = Depends(get_session)):
    # 1. Формируем запрос: "Выбрать всё из таблицы Hero, где имя совпадает"
    statement = select(Hero).where(Hero.name == name)
    
    # 2. Выполняем запрос и берем первый результат
    hero = session.exec(statement).first()
    
    # 3. Если герой не найден — возвращаем 404 ошибку
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден в этом подземелье")
    
    return hero

@app.get('/heroes/')
def get_all_heroes(session: Session = Depends(get_session)):

    statement = select(Hero)

    hero = session.exec(statement).all()

    if not hero : 
        raise HTTPException(status_code=404, detail="Нет доступных героев")
    
    return hero

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
    # 1. Ищем героя
    db_hero = session.exec(select(Hero).where(Hero.name == name)).first()
    if not db_hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    # 2. Превращаем присланные данные в словарь, исключая те, что не прислали (None)
    update_dict = hero_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        # 3. Базовая логика ограничений (пример для HP)
        if key == "current_hp":
            # Не даем упасть ниже 0 и подняться выше макс_хп
            value = max(0, min(value, db_hero.max_hp))
        
        if key == "gold":
            # Золото не может быть отрицательным
            value = max(0, value)

        # Применяем изменение к объекту
        setattr(db_hero, key, value)

    # 4. Сохраняем
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@app.post("/heroes/{name}/full_heal")
def hero_full_heal(name: str, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    
    heal_cost = 10
    if hero.gold < heal_cost:
        raise HTTPException(status_code=400, detail="Нужно больше золота!")
    
    if hero.current_hp == hero.max_hp:
        return {"message": "Герой уже полностью здоров"}

    hero.gold -= heal_cost
    hero.current_hp = hero.max_hp # Лечим до максимума
    
    session.add(hero)
    session.commit()
    return {"message": "Вы провели ночь в Таверне.  Здоровье полностью восстановлено.", "gold_left": hero.gold}

@app.post("/heroes/{name}/spell/heal")
def spell_heal(name: str, session: Session = Depends(get_session)):
    hero = session.exec(select(Hero).where(Hero.name == name)).first()
    base_power= 5
    spell_power= base_power + hero.intelligence

    mp_cost = 1
    if hero.current_mp < mp_cost:
        return {"message": "Недостаточно МP"}
    if hero.current_hp == hero.max_hp:
        return {"message": "Герой уже полностью здоров"}
    
    hero.current_mp -= mp_cost

    if hero.current_hp + spell_power > hero.max_hp:
        hero.current_hp = hero.max_hp
        
    else : hero.current_hp+=spell_power

    session.add(hero)
    session.commit()
    session.refresh(hero)

    return {
        "message": (
            f" {hero.name} шепчет заклинание... Восстановлено {spell_power} HP. "
            f"Текущее состояние: {hero.current_hp}/{hero.max_hp} HP, {hero.current_mp}/{hero.max_mp} MP."
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
    # 1. Формируем запрос: "Выбрать всё из таблицы Hero, где имя совпадает"
    statement = select(Monster).where(Monster.name == name)
    
    # 2. Выполняем запрос и берем первый результат
    monster = session.exec(statement).first()
    
    # 3. Если герой не найден — возвращаем 404 ошибку
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

    # 2. Превращаем присланные данные в словарь, исключая те, что не прислали (None)
    update_dict = monster_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        # 3. Базовая логика ограничений (пример для HP)
        if key == "current_hp":
            # Не даем упасть ниже 0 и подняться выше макс_хп
            value = max(0, min(value, db_monster.max_hp))
        

        # Применяем изменение к объекту
        setattr(db_monster, key, value)

    # 4. Сохраняем
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



@app.get("/world/explore/{hero_name}")
def explore(hero_name: str, session: Session = Depends(get_session)):
    # 1. Ищем героя
    hero = session.exec(select(Hero).where(Hero.name == hero_name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")

    ## 2. Берем случайного монстра, подходящего по уровню (+-1)
    # Формируем запрос с фильтрацией
    statement = (
        select(Monster)
        .where(Monster.level >= hero.level - 1) # Минимум (уровень героя - 1)
        .where(Monster.level <= hero.level + 1) # Максимум (уровень героя + 1)
        .order_by(func.random())
        .limit(1)
    )
    
    monster = session.exec(statement).first()

    if not monster:
        return {
            "message": f"В этой части подземелья слишком спокойно для героя {hero.level} уровня. Монстров подходящей силы не нашлось."
        }
    return {
        "event": f"Из тени появляется {monster.name}!",
        "hero_level": hero.level,
        "monster_level": monster.level,
        "monster_stats": {
            "hp": monster.max_hp,
            "attack": f"{monster.min_attack}-{monster.max_attack}"
        }
    }

@app.post("/battle/attack/{hero_name}/{monster_id}")
def battle_round(hero_name: str, monster_id: int, session: Session = Depends(get_session)):
    # 1. Загружаем участников
    hero = session.exec(select(Hero).where(Hero.name == hero_name)).first()
    monster = session.exec(select(Monster).where(Monster.id == monster_id)).first()

    if not hero or not monster:
        raise HTTPException(status_code=404, detail="Участники боя не найдены")

    log = [] # Сюда будем записывать ход боя для f-строки

    # 2. Определяем очередность (Инициатива)
    hero_goes_first = hero.level >= monster.level

    def hero_attack():
        # Формула: STR + random(DEX/2)
        dex_bonus = random.randrange(max(1, hero.dexterity // 2))
        damage = hero.strength + dex_bonus
        
        # Проверка на уклонение монстра (допустим у моба 5% фикс или добавим ему agi позже)
        monster.current_hp -= damage
        log.append(f"⚔️ {hero.name} наносит {damage} урона! (HP моба: {max(0, monster.current_hp)})")

    def monster_attack():
        # Проверка на уклонение героя: 1 AGI = 1% шанса
        if random.randint(1, 100) <= hero.agility:
            log.append(f"💨 {hero.name} изящно уклонился от атаки {monster.name}!")
            return

        damage = random.randint(monster.min_attack, monster.max_attack)
        hero.current_hp -= damage
        log.append(f"💥 {monster.name} кусает за бочок на {damage} урона! (Твое HP: {max(0, hero.current_hp)})")

    # --- САМ БОЙ (Один раунд) ---
    if hero_goes_first:
        hero_attack()
        if monster.current_hp > 0:
            monster_attack()
    else:
        monster_attack()
        if hero.current_hp > 0:
            hero_attack()

    # 3. ПРОВЕРКА ИСХОДА
    
    # ЕСЛИ УМЕР ГЕРОЙ
    if hero.current_hp <= 0:
        hero_name = hero.name
        session.delete(hero) # "Hardcore" режим - удаляем из базы
        session.commit()
        return {"status": "DEATH", "log": log, "message": f"💀 Герой {hero_name} пал в бою. Игра окончена."}

    # ЕСЛИ УМЕР МОНСТР
    if monster.current_hp <= 0:
        gold_gain = random.randint(monster.min_gold, monster.max_gold)
        hero.gold += gold_gain
        hero.xp += monster.xp_reward
        
        # Логика Level Up (упрощенно: каждые 100 XP - новый уровень)
        lvl_up_msg = ""
        if hero.xp >= hero.level * 100:
            hero.level += 1
            hero.dexterity+=1
            hero.agility+=1
            hero.strength+=1
            hero.intelligence+=1
            hero.vitality+=1
            hero.max_hp += 20
            hero.current_hp = hero.max_hp # Лечим при апе
            lvl_up_msg = f" 🎉 УРОВЕНЬ ПОВЫШЕН! Теперь ты {hero.level} уровня!"

        # Сбрасываем HP монстра для следующей встречи (т.к. мы используем шаблон из базы)
        monster.current_hp = monster.max_hp
        
        session.add(hero)
        session.commit()
        return {
            "status": "VICTORY", 
            "log": log, 
            "reward": f"💰 +{gold_gain} золота, ✨ +{monster.xp_reward} опыта.{lvl_up_msg}"
        }

    # ЕСЛИ ОБА ЖИВЫ
    session.add(hero)
    session.add(monster)
    session.commit()
    return {"status": "CONTINUE", "log": log}
    
