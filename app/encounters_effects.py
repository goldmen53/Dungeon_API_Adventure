from sqlmodel import Session, select
from app.models import Hero
from fastapi import HTTPException
import random
from app.utils import hero_overflow_check


def encounter_give_any_stat(hero, session: Session, stat: str):
    
    hero = session.exec(select(Hero).where(Hero.name == hero.name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Герой не найден")
     
    if stat == "str" and hero.strength < 50:
        hero.strength += 1
    elif stat == "agi" and hero.agility <50: 
        hero.agility += 1
    
    elif stat == "vit" and hero.vitality < 50:
        hero.vitality += 1
        # Сразу обновляем макс ХП по  формуле 
        hero.hp += (hero.vitality*10)
        if hero.hp > hero.max_hp:
            hero.hp = hero.max_hp
    
    elif stat == "int" and hero.intelligence < 50:
        hero.intelligence += 1
    elif stat == "dex" and hero.dexterity < 50:
        hero.dexterity += 1

    else:
        
        return "Вы уже и так очень искустны в этой области " 
    

    hero.active_event_id = None  # Разблокируем героя
    session.add(hero)
   
    
    return f"Статистика {stat} увеличена!"

def effect_altar_sacrifice(hero, session, choice):
    if choice == "sacrifice":
        if hero.hp <= 30:
            raise HTTPException(status_code=400, detail="Слишком слаб для жертвы!")
        
        if hero.strength >= 50:
            msg = "Вы уже и так слишком сильны"
        else:
            hero.strength += 2
            hero.hp -= 30
            msg = "Алтарь выпил вашу кровь, но наполнил мышцы сталью.(-30 HP, +2 strength)"

    if choice == 'pray' :
        hero.mp = min(hero.max_mp, hero.mp + 10)
        msg = "Вы тихо помолились и почувствовали покой.(SP+10)"
    
    hero_overflow_check(hero)
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
            msg = f"Вы угадали! Гоблин ворчит и отдает мешочек монет.(gold+{bet})"
        else:
            hero.gold = max(0, hero.gold - bet)
            msg = f"Не повезло! Гоблин ловко срезал ваш кошелек и убежал.(gold-{bet})"
    if choice == 'go_away':
        msg = "Вы прошли мимо. Азарт — это путь к нищете."
    
    hero.active_event_id = None
    return msg

def effect_ancient_library(hero, session, choice):
    
    damage = 10
    if choice == "reach":
        if hero.agility >= random.randrange(10,16):
            hero.agility += 1
            msg = "Вы ловко взобрались по стеллажам и изучили свиток!(agi+1)"
            if hero.agility >=50:

                hero.agility = 50 
                msg = "Вы ловко взобрались по стеллажам и изучили свиток,но все это вы и так знали!"
        else:
            if hero.hp < damage:
                hero.hp = 1
                msg = f"Стеллаж рухнул прямо на вас. Больно... и чуть не убил вас (HP - {damage}) "
            else :
                hero.hp -= damage
                msg = f"Стеллаж рухнул прямо на вас. Больно... Вы ушиблись и потеряли {damage} "



    elif choice == "decode":
        if hero.intelligence >= random.randrange(10,16):
            hero.intelligence += 1
            msg = "Сложные знаки сложились в знания. Вы стали мудрее.( int +1)"
            if hero.intelligence >=50:
                hero.intelligence =50 
                msg = "Сложные знаки сложились в знания, но все это вы и так знали "

            
        else:
            msg = "Текст кажется бессмысленным набором каракуль.Вам ,кажется ,что вы немного поглупели.(int-1)"
            hero.intelligence -= 1
            if hero.intelligence <= 1:
                hero.intelligence = 1 
                if hero.hp < damage:
                    hero.hp = 1
                    msg = f"Вам больно осозновать что вы настолько глупы. Вы получете урон по самолюбию, настолько что вы почти теряете сознание (HP -{damage})"
                else :
                    hero.hp -= damage
                    msg = f"Вам больно осозновать что вы настолько глупы. Вы получете урон по самолюбию.Вы теряете  {damage} hp из-за ментального состояния "
                
    
    hero.active_event_id = None
    return msg

def effect_strange_mirror(hero,session,choice):
    gold_bag = 20
    tablet = 3
    scare =20


    if choice == "look_closer": #при выборе : дает 1/2 от максимальных хп и мп , но обнуляет опыт героя
        if hero.hp < hero.max_hp:
           if hero.hp + int(hero.max_hp /2) > hero.max_hp:
                hero.hp == hero.max_hp
           else :
                hero.hp += int(hero.max_hp /2)
        
        if hero.mp < hero.max_mp:
           if hero.mp + int(hero.max_mp /2) > hero.max_mp:
                hero.mp == hero.max_mp
           else :
                hero.mp += int(hero.max_mp /2)

        hero_overflow_check(hero)

        if hero.xp > 0 :
            hero.xp = 0 

        msg= ("В отражении ваше лицо выглядит моложе!И вы даже ощущяете себя моложе! Но вам кажеться что вы что-то забили... (Вы восполняете коловину MP и HP,но опыт текущего уровня обнуляеться )" )
        

    if choice == "crash_mirror":

        hero.gold += gold_bag 
        hero.agility+= tablet
        
        if hero.hp < scare:
            hero.hp = 1 
        else:
            hero.hp -= scare

        hero_overflow_check(hero)

        
        hero.max_mp -= 3
        if hero.max_mp < 1:
            hero.max_mp = 1 
        msg=f"Вы разбиваете зеркало рукояткой совего кинжала.Часть осколков впиваеться вам в руку, но кроме осколков в чуете-то под кожу проникло кое-что ещё ,что блокирует вашу маг.энергию. За остатками зеркала вы обнаруживаете нижу в которой лежит кошел с деньгами и табличка со знаниями о воровском деле (gold +{gold_bag}, agi+{tablet} max_sp -3 ) "


    if choice =="go_forward":
        hero.mp -=5
        hero_overflow_check(hero)
        msg= "Вы думаете ,что зеркало слишком подозрительно выглядит и  решаете пройти мимо. Как только вы отварачиваетесь появлеться ощущение как-будто вам смотрет в спину. Впрочем, через пару шагов ощущение пропадает.(Вы теряете 5 SP)   "
    return msg

# Реестр: связываем строку из БД с функцией
ENCAUNTERS_EFFECTS = {
    "give_any_stat": encounter_give_any_stat,
    "altar_event": effect_altar_sacrifice,
    "goblin_event": effect_goblin_gamble,
    "library_event": effect_ancient_library,
    "mirror_event": effect_strange_mirror
}