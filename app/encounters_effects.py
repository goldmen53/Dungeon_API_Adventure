from sqlmodel import Session, select
from app.models import Hero
from fastapi import FastAPI, Depends, HTTPException
from app.database import init_db, get_session
import random


def encaunter_give_any_stat(hero, session: Session, stat: str):
    
    hero = session.exec(select(Hero).where(Hero.name == hero.name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
     
    if stat == "str" and hero.strength <= 50:
        hero.strength += 1
    elif stat == "agi" and hero.agility <=50: 
        hero.agility += 1
    
    elif stat == "vit" and hero.vitality <= 50:
        hero.vitality += 1
        # Сразу обновляем макс ХП по  формуле 
        hero.hp += (hero.vitality*10)
        if hero.hp > hero.max_hp:
            hero.hp = hero.max_hp
    
    elif stat == "int" and hero.intelligence <= 50:
        hero.intelligence += 1
    elif stat == "dex" and hero.dexterity <= 50:
        hero.dexterity += 1

    else:
        raise HTTPException(status_code=400, detail="Неверная характеристика")
    

    hero.active_event_id = None  # Разблокируем героя
    session.add(hero)
   
    
    return f"Статистика {stat} увеличена!"

def effect_altar_sacrifice(hero, session, choice):
    if choice == "sacrifice":
        if hero.hp <= 30:
            raise HTTPException(status_code=400, detail="Слишком слаб для жертвы!")
        hero.hp -= 30

        hero.strength += 2
        if hero.streenght > 50:
            hero.hero.strength = 50
        msg = "Алтарь выпил вашу кровь, но наполнил мышцы сталью."
    else:
        hero.mp = min(hero.max_mp, hero.mp + 10)
        msg = "Вы тихо помолились и почувствовали покой."
    
    hero.active_event_id = None
    return msg

def effect_goblin_gamble(hero, session, choice):
    if choice == "play":

        bet = 10
        if hero.gold < bet:
            msg = 'У Вас недостаточно золота для игры'
            hero.active_event_id = None
            return msg

        if random.random() > 0.5:
            hero.gold += bet
            msg = "Вы угадали! Гоблин ворчит и отдает мешочек монет."
        else:
            hero.gold = max(0, hero.gold - bet)
            msg = "Не повезло! Гоблин ловко срезал ваш кошелек и убежал."
    else:
        msg = "Вы прошли мимо. Азарт — это путь к нищете."
    
    hero.active_event_id = None
    return msg

def effect_ancient_library(hero, session, choice):
    if choice == "reach":
        if hero.agility >= random.randrange(10,16):
            hero.agility += 1
            if hero.agility >50:
                hero.agility = 50 

            msg = "Вы ловко взобрались по стеллажам и изучили свиток!"
        else:
            hero.hp -= 10
            msg = "Стеллаж рухнул прямо на вас. Больно..."
    elif choice == "decode":
        if hero.intelligence >= random.randrange(10,16):
            hero.intelligence += 1
            if hero.intelligence >50:
                hero.intelligence = 50 

            msg = "Сложные знаки сложились в знания. Вы стали мудрее."
        else:
            msg = "Текст кажется бессмысленным набором каракуль."
    
    hero.active_event_id = None
    return msg



# Реестр: связываем строку из БД с функцией
ENCAUNTERS_EFFECTS = {
    "give_any_stat": encaunter_give_any_stat,
    "altar_event": effect_altar_sacrifice,
    "goblin_event": effect_goblin_gamble,
    "library_event": effect_ancient_library
}