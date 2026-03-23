from sqlmodel import Session, select
from app.models import Hero
from fastapi import HTTPException
import random
from app.utils import hero_overflow_check


def encounter_give_any_stat(hero, session: Session, stat: str):
    
    hero = session.exec(select(Hero).where(Hero.name == hero.name)).first()
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
     
    if stat == "str" and hero.strength < 50:
        hero.strength += 1
    elif stat == "agi" and hero.agility <50: 
        hero.agility += 1
    
    elif stat == "vit" and hero.vitality < 50:
        hero.vitality += 1
        # Immediately update max HP by formula
        hero.hp += (hero.vitality*10)
        if hero.hp > hero.max_hp:
            hero.hp = hero.max_hp
    
    elif stat == "int" and hero.intelligence < 50:
        hero.intelligence += 1
    elif stat == "dex" and hero.dexterity < 50:
        hero.dexterity += 1

    else:
        
        return "You are already very skilled in this area"
    

    hero.active_event_id = None  # Unlock hero
    session.add(hero)
   
    
    return f"Stat {stat} increased!"

def effect_altar_sacrifice(hero, session, choice):
    if choice == "sacrifice":
        if hero.hp <= 30:
            raise HTTPException(status_code=400, detail="Too weak for sacrifice!")
        
        if hero.strength >= 50:
            msg = "You are already too strong"
        else:
            hero.strength += 2
            hero.hp -= 30
            msg = "The altar drank your blood but filled your muscles with steel.(-30 HP, +2 strength)"

    if choice == 'pray' :
        hero.mp = min(hero.max_mp, hero.mp + 10)
        msg = "You quietly prayed and felt peace.(SP+10)"
    
    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_goblin_gamble(hero, session, choice):
    if choice == "play":

        bet = 10
        if hero.gold < bet:
            msg = 'You don\'t have enough gold to play'
            hero.active_event_id = None
            return msg

        if random.random() > 0.5:
            hero.gold += bet
            msg = f"You guessed right! The goblin grumbles and hands over the coin bag.(gold+{bet})"
        else:
            hero.gold = max(0, hero.gold - bet)
            msg = f"Bad luck! The goblin cleverly cut your purse and ran away.(gold-{bet})"
    if choice == 'go_away':
        msg = "You walked past. Gambling is the path to poverty."
    
    hero.active_event_id = None
    return msg

def effect_ancient_library(hero, session, choice):
    
    damage = 10
    if choice == "reach":
        if hero.agility >= random.randrange(10,16):
            hero.agility += 1
            msg = "You nimbly climbed the shelves and studied the scroll!(agi+1)"
            if hero.agility >=50:

                hero.agility = 50 
                msg = "You nimbly climbed the shelves and studied the scroll, but you already know all this!"
        else:
            if hero.hp < damage:
                hero.hp = 1
                msg = f"The bookshelf collapsed right on you. It hurts... and almost killed you (HP - {damage}) "
            else :
                hero.hp -= damage
                msg = f"The bookshelf collapsed right on you. It hurts... You got hurt and lost {damage} "



    elif choice == "decode":
        if hero.intelligence >= random.randrange(10,16):
            hero.intelligence += 1
            msg = "The complex signs formed into knowledge. You became wiser.( int +1)"
            if hero.intelligence >=50:
                hero.intelligence = 50 
                msg = "The complex signs formed into knowledge, but you already know all this "
            
        else:
            msg = "The text seems like meaningless scribbles. You feel like you got a bit stupider.(int-1)"
            hero.intelligence -= 1
            if hero.intelligence <= 1:
                hero.intelligence = 1 
                if hero.hp < damage:
                    hero.hp = 1
                    msg = f"It hurts to realize how stupid you are. You take mental damage that almost knocks you out (HP -{damage})"
                else :
                    hero.hp -= damage
                    msg = f"It hurts to realize how stupid you are. You lose {damage} hp due to mental state "
                
    
    hero.active_event_id = None
    return msg

def effect_strange_mirror(hero,session,choice):
    gold_bag = 20
    tablet = 3
    scare =20


    if choice == "look_closer": #gives 1/2 of max HP and MP but resets hero XP
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

        msg= ("Your reflection looks younger! You even feel younger! But you feel like you forgot something... (You restore half MP and HP, but current level XP is reset)")
        

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
        
        msg=f"You smash the mirror with your dagger handle. Some shards embed in your hand, but something else penetrated your skin, blocking your magical energy. Among the mirror remnants you find a pouch of gold and a tablet of thieves' knowledge (gold +{gold_bag}, agi+{tablet}, max_sp -3 HP-{scare}) "
        hero_overflow_check(hero)

    if choice =="go_forward":
        hero.mp -=5
        hero_overflow_check(hero)
        msg= "You think the mirror looks too suspicious and decide to walk past. As you turn away, you feel like something is watching your back. After a couple steps the feeling disappears.(You lose 5 SP)   "
    hero.active_event_id = None
    return msg

def effect_mushroom_event(hero,sesion,choice):
    if choice == "eat_red":

        if hero.hp == hero.max_hp:
            hero.vitality += 2 
            
            msg = "You see a white rabbit in the distance of the labyrinth, but blinking you realize it was just your imagination. You feel much more energetic. (vit +2)"
        else:
            
            hero.vitality += 1 
            hero.hp = hero.max_hp
            msg = "You see a white rabbit in the distance of the labyrinth, but blinking you realize it was just your imagination. Your wounds healed and you feel a bit more energetic. (HP restored, vit+1)"
             


    if choice == "eat_blue":
        if hero.mp == hero.max_mp:
            hero.max_mp += 5
            msg = "You feel your magical capacity has increased (max_mp +5)"
        else:
            hero.max_mp += 3
            hero.mp= hero.max_mp
            msg = "Your magical forces restored and you feel your magical capacity has increased (SP restored max_mp +3)"


    if choice == "trample_mushrooms":

        hero.mp =hero.max_mp
        hero.hp =hero.max_hp
        msg = 'You ruthlessly step on the mushrooms! You inhale the spores of crushed mushrooms and pass out. Upon waking you feel well rested! (Your MP and HP are fully restored)'
        
    if choice == "go_forward":
        msg="You walk past"




    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_wishing_well(hero,sesion,choice):
    if choice == "toss_coin":
        
        if hero.gold < 1:
            msg= 'Searching your pockets you realize you don\'t have a single coin to throw in the well. Shrugging, you walk on'
        else:
            hero.gold -= 10 
            if hero.gold < 0:
                hero.gold = 0
            if random.random() > 0.4:
                hero.gold += 50
                msg = "You threw the coins and stared into the abyss of the well. After a few seconds you heard the coins splash. You were about to go on your way when you heard another splash and after a couple seconds a wet pouch full of gold fell to the ground(gold+50)"
            else:
                msg = "You threw the coins and stared into the abyss of the well, but no matter how long you waited no sounds came from the well..."


    if choice == "toss_rock":
        damage =25
        if random.random() > 0.5:
            msg= f"You threw a rock and stared into the abyss of the well. After a couple seconds a bigger rock flew out of the well and hit your eyebrow. From the well comes dissatisfied grumbling (-{damage} HP)"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage
        
        else: 
            msg= f"You threw a rock and stared into the abyss of the well. After a couple seconds something flew out of the well towards you and hit your eyebrow. Looking closer you see it's a tablet of knowledge (-{damage} HP, dex +3)"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage
            hero.dexterity +=3


    if choice == "spit":
        if random.random() > 0.5:
            msg = "You spit in the well and nothing happens"
        else:
            msg = "You spit in the well and in return something flies out of the depths at you. Surprisingly your morale suffered but you feel better (HP and SP slightly restored)"
            hero.hp +=50
            hero.mp +=25
    if choice == "look_inside":
        if hero.agility > 15:
            if random.random() > 0.5:
                hero.strength += 2 
                msg = "You look into the well and see a magical tablet between the stones. You try to retrieve it and succeed!(str+2)"
            else:
                msg = "You look into the well and see a magical tablet between the stones. You try to retrieve it, but the tablet slips from your hands and falls into the abyss..."
        else:
            msg = "You look into the well, but only see oppressive darkness"

    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_cocoon(hero,sesion,choice):
    damage = 50
    if choice == "cut":
        if random.random() > 0.5:
            msg = "You save the thief, who in gratitude gives you all his gold (gold +15)"
            hero.gold +=15
        else:
            msg =f"A swarm of tiny spiders bursts from the cocoon! You defended yourself but they got a good bite on you ( -{damage} HP, +10xp)"
            if hero.hp <= damage:
                hero.hp = 1 
            else:
                hero.hp -= 50
            hero.xp += 10


    if choice == "ignore":
        msg = "You walk past"
    
    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_burnt_chest(hero,sesion,choice):

    damage = 50

    if choice == "open_str":
        if hero.strength >= random.randrange(10,20):
            
            msg = "Under your barrage of attacks the chest falls apart. Inside is a pouch with health potion and some gold(HP restore +10 gold)"
            hero.hp = hero.max_hp
            hero.gold +=15
        else:
            msg = f"After your barrage of attacks the chest still doesn't give in. You got tired and your hands are bleeding, but it was great training!(HP-{damage}, XP+5)"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage

    if choice == "open_agi":
        if hero.agility >= random.randrange(10,20):
            msg = "You cleverly pick the lock, but the chest is completely empty!"
        else:
            msg = f"You try to pick the lock, but the lockpick breaks and you hear hissing. You try to run but the explosion catches you!(HP-{damage})"
            if hero.hp <= damage:
                hero.hp = 1
            else:
                hero.hp -= damage


    if choice == "ignore":
        if random.random() > 0.9:
            msg = "As you walk past the chest behind you catches fire! After it burns out you find a tablet of knowledge from the ashes (int +1)"
            hero.intelligence +=1 
        else:
            msg = "You walk past"
    
    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

def effect_cook(hero,sesion,choice):
    if choice =="try":
        if hero.gold < 1:
            msg = "Searching your pockets you realize you don\'t have a single gold to pay for soup. Shrugging, you walk on" 
        else:
            hero.gold -= 1
            if random.random() > 0.5:
                msg ="The goblin gives you a bowl of soup and it looks good! You eat it and your strength is restored.(HP +70, MP +10)"
                hero.hp +=70
                hero.mp +=10
            else:
                msg = "The goblin gives you a bowl of soup and it looks quite edible! You eat it and the hunger goes away, but after a while you feel some burning in your stomach(HP +40, MP -10)"
                hero.hp +=40
                hero.mp -=10
            
    if choice =="ignore":
        if random.random() > 0.8:
            msg = "You ignore the goblin and just walk past. Behind you hear incoherent grumbling. Then he gives you a piece of dough. Walking away you try it. And it\'s very tasty! Your mood improved (HP +20, MP +5) "
            hero.hp +=20
            hero.mp +=5

    hero_overflow_check(hero)
    hero.active_event_id = None
    return msg

# Registry: link string from DB with function
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
    "cook_event":effect_cook
    
}