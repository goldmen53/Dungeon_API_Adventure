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

        

        
        hero.max_mp -= 3
        if hero.max_mp < 1:
            hero.max_mp = 1 
        
        msg=f"Вы разбиваете зеркало рукояткой совего кинжала.Часть осколков впиваеться вам в руку, но кроме осколков в чуете-то под кожу проникло кое-что ещё ,что блокирует вашу маг.энергию. За остатками зеркала вы обнаруживаете нижу в которой лежит кошел с деньгами и табличка со знаниями о воровском деле (gold +{gold_bag}, agi+{tablet} ,max_sp -3 HP-{scare} ) "
        hero_overflow_check(hero)

    if choice =="go_forward":
        hero.mp -=5
        hero_overflow_check(hero)
        msg= "Вы думаете ,что зеркало слишком подозрительно выглядит и  решаете пройти мимо. Как только вы отварачиваетесь появлеться ощущение как-будто вам смотрет в спину. Впрочем, через пару шагов ощущение пропадает.(Вы теряете 5 SP)   "
    hero.active_event_id = None
    return msg

def effect_mushroom_event(hero,sesion,choice):
    if choice == "eat_red":

        if hero.hp == hero.max_hp:
            hero.vitality += 2 
            
            msg = "Вы видете белого кролика вдали лабиринта, но проморгавшись вы поняли, что вам просто показалось. Вы чувствуете себя гораздо бодрее. (vit +2)"
        else:
            
            hero.vitality += 1 
            hero.hp = hero.max_hp
            msg = "Вы видете белого кролика вдали лабиринта, но проморгавшись вы поняли, что вам просто показалось.Ваши раны затянулись и вы почуствовали себя немного бодрее. (HP востановленно, vit+1)"
             


    if choice == "eat_blue":
        if hero.mp == hero.max_mp:
            hero.max_mp += 5
            msg = "Вы чувствуете что ваша магическая емкость увеличилась (max_mp +5)"
        else:
            hero.max_mp += 3
            hero.mp= hero.max_mp
            msg = "Ваши магически силы востановились и вы чувствуете что ваша магическая емкость увеличилась (SP востановленно max_mp +3)"


    if choice == "trample_mushrooms":

        hero.mp =hero.max_mp
        hero.hp =hero.max_hp
        msg = 'Вы безжалостно давите грибы ногами! Вы вдыхаете споры раздавленых грибов и падаете без сознания. Очнувшись вы чувствуете что хорошо отдохнули! (Ваши MP и HP полностью востановлены)'
        
    if choice == "go_forward":
        msg="Вы проходите мимо"





    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_wishing_well(hero,sesion,choice):
    if choice == "toss_coin":
        
        if hero.gold < 1:
            msg= 'Пошарив по карманам вы поняли , что у вас нет ни одной монеты , которую можно бросить в колодец.Пожав плечами вы пошли дальше'
        else:
            hero.gold -= 10 
            if hero.gold < 0:
                hero.gold = 0
            if random.random() > 0.4:
                hero.gold += 50
                msg = "Вы бросили конеты и уставилсь в бездну колодца, через несколько сукунт вы услышали как монеты плюхнулись в воду.Вы уже собирались пойти по своим делам , но услышали новый всплеск в колодце и через пару секунд на замлю упал мокрый мешочек полный золота"
            else:
                msg = "Вы бросили конеты и уставилсь в бездну колодца, но сколько вы бы не ждали никаких звуков из колодца так и не раздалось..."


    if choice == "toss_rock":
        damage =25
        if random.random() > 0.5:
            msg= f"Вы бросили камень и уставилсь в бездну колодца, через пару секунд из глубины кододца в на встречу к вас вылетел ещё больший камень и расшиб вам бровь.Из колодца доносеться недовольное ворчание (-{damage} HP)"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage
        
        else: 
            msg= f"Вы бросили камень и уставилсь в бездну колодца, через пару секунд из глубины кододца в на встречу к вас вылетел какой-то обект и расшиб вам бровь.Вы присмотревшись вы понимаете что это табличка знаний (-{damage} HP, dex +3)"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage
            hero.dexterity +=3


    if choice == "spit":
        if random.random() > 0.5:
            msg = "Вы плюете в колодец и ничего не произходит"
        else:
            msg = "Вы плюете в колодец и в ответ из глубины вам тоже прилетает плевок. Удивительно хоть ваша мораль и пострадала, но вы чувствуете себя лучше (HP и SP немного востановлены)"
            hero.hp +=50
            hero.mp +=25
    if choice == "look_inside":
        if hero.agility > 15:
            if random.random() > 0.5:
                hero.strength += 2 
                msg = "Вы заглядываете в колодец и видите между камнями магическую табличку вы стараетесь её достать и у вас получаеться!(str+2)"
            else:
                msg = "Вы заглядываете в колодец и видите между камнями магическую табличку вы стараетесь её достать, но табличка выскальзывает у вас с рук и падает в бездну..."
        else:
            msg = "Вы заглядываете в колодец, но видите только гнетущую темноту"

    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_cocoon(hero,sesion,choice):
    damage = 50
    if choice == "cut":
        if random.random() > 0.5:
            msg = "Ты спасаешь вора, который в благодарность он отдает тебе все свое золото (gold +15)"
            hero.gold +=15
        else:
            msg =f"Из кокона вырывается рой мелких пауков! Вы отбились , но они успели здорово вас покусать ( -{damage} HP, +10xp)"
            if hero.hp <= damage:
                hero.hp = 1 
            else:
                hero.hp -= 50
            hero.xp += 10


    if choice == "ignore":
        msg = "Вы проходите мимо"
    
    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_burnt_chest(hero,sesion,choice):

    damage = 50

    if choice == "open_str":
        if hero.strength >= random.randrange(10,20):
            
            msg = "Под градом ваших ударов сундук рассыпается в нем лежит пузерек с зельем здоровья и немного золотых(HP restore +10 gold)"
            hero.hp = hero.max_hp
            hero.gold +=15
        else:
            msg = f"После градов ваших ударов сундук никак не поддаеться. Вы вымотались и ваши руки кровоточат ,но это была отличная тренировка!(HP-{damage}, XP+5)"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage

    if choice == "open_agi":
        if hero.agility >= random.randrange(10,20):
            msg = "Вы ловко вскрываете замок, но сундук полостю пуст!"
        else:
            msg = f"Вы пытаетесь вскрыть сундук , но отмычка ломаеться и вы слышите шипение.Вы пытаетесь отбежать, но не успеваете взрыв задевает вас!(HP-{damage})"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage


    if choice == "ignore":
        if random.random() > 0.9:
            msg = "Когда вы проходите мимо сундук за вашей спиной загораеться! После того как он догорел из углей вы достали табличку знаний (int +1)"
            hero.intelligence +=1 
        else:
            msg = "Вы проходите мимо"
    
    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_cook(hero,sesion,choice):
    if choice =="try":
        if hero.gold < 1:
            msg = "Покапавшись в карманах вы поняли , что у вас нет не одного золотого, что б заплтить за суп. Пожав плечами вы пошли дальше" 
        else:
            hero.gold -= 1
            if random.random() > 0.5:
                msg ="Гоблин дает вам тарелку супа , и она выглядит неплохо! Вы съели и ваши сили востановились.(HP +70, MP +10)"
                hero.hp +=70
                hero.mp +=10
            else:
                msg = "Гоблин дает вам тарелку супа, и она выглядит вполне съедобной! Вы сьели и чувство голода прошло ,но через время вы почуствовали какое-то жжение в животе(HP +40, MP -10)"
                hero.hp +=40
                hero.mp -=10
            
    if choice =="ignore":
        if random.random() > 0.8:
            msg = "Вы игнорируете гоблина и просто прходите мимо, За спиной слышите невнятное ворчание"
        else: 
            msg = "Вы пытаетесь пройти мимо, но гоблин настойчиво пытаеться вам что-то всучить.Он дает вам кусок сдобного теста. Отойдя подальше вы пробуете его.И это очень вкустно! Ваше настроение улучшилось (HP +20, MP +5) "
            hero.hp +=20
            hero.mp +=5

    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

# Реестр: связываем строку из БД с функцией
ENCAUNTERS_EFFECTS = {
    "give_any_stat": encounter_give_any_stat,
    "altar_event": effect_altar_sacrifice,
    "goblin_event": effect_goblin_gamble,
    "library_event": effect_ancient_library,
    "mirror_event": effect_strange_mirror,
    "mushroom_event": effect_mushroom_event,
    "wishing_well_event": effect_wishing_well,
    "cocoon_event": effect_cocoon,
    "burnt_chest_event" : effect_burnt_chest,
    "сook_event":effect_cook
    
}