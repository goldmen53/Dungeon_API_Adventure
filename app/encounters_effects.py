from sqlmodel import Session, select
from app.models import Hero
from fastapi import HTTPException
import random


def encounter_give_any_stat(hero, session: Session, stat: str):
    
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
        if hero.strength > 50:
            hero.hero.strength = 50
        msg = "Алтарь выпил вашу кровь, но наполнил мышцы сталью."
    if choice == 'pray' :
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
    if choice == 'go_away':
        msg = "Вы прошли мимо. Азарт — это путь к нищете."
    
    hero.active_event_id = None
    return msg

def effect_ancient_library(hero, session, choice):
    
    damage = 10
    if choice == "reach":
        if hero.agility >= random.randrange(10,16):
            hero.agility += 1
            msg = "Вы ловко взобрались по стеллажам и изучили свиток!"
            if hero.agility >=50:

                hero.agility = 50 
                msg = "Вы ловко взобрались по стеллажам и изучили свиток,но все это вы и так знали!"
        else:
            if hero.hp < damage:
                hero.hp = 1
                msg = f"Стеллаж рухнул прямо на вас. Больно... и чуть не убил вас "
            else :
                hero.hp -= damage
                msg = f"Стеллаж рухнул прямо на вас. Больно... Вы ушиблись и потеряли {damage} "



    elif choice == "decode":
        if hero.intelligence >= random.randrange(10,16):
            hero.intelligence += 1
            msg = "Сложные знаки сложились в знания. Вы стали мудрее."
            if hero.intelligence >=50:
                hero.intelligence =50 
                msg = "Сложные знаки сложились в знания, но все это вы и так знали "

            
        else:
            msg = "Текст кажется бессмысленным набором каракуль.Вам кажеться что вы немного поглупели"
            hero.intelligence -= 1
            if hero.intelligence <= 1:
                hero.intelligence = 1 
                if hero.hp < damage:
                    hero.hp = 1
                    msg = f"Вам больно осозновать что вы настолько глупы. Вы получете урон по самолюбию, настолько что вы почти теряете сознание"
                else :
                    hero.hp -= damage
                    msg = f"Вам больно осозновать что вы настолько глупы. Вы получете урон по самолюбию.Вы теряете  {damage} hp из-за ментального стстояния "
                
    
    hero.active_event_id = None
    return msg



# Реестр: связываем строку из БД с функцией
ENCAUNTERS_EFFECTS = {
    "give_any_stat": encounter_give_any_stat,
    "altar_event": effect_altar_sacrifice,
    "goblin_event": effect_goblin_gamble,
    "library_event": effect_ancient_library
}