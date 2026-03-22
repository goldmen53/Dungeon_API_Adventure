import random
def effect_vampirism(hero, monster, damage):
    heal = int(damage * 0.15)
    hero.hp = min(hero.max_hp, hero.hp + heal)
    return f"Вампиризм: +{heal} HP"

def effect_berserk(hero, monster, damage):
    if hero.hp < (hero.max_hp * 0.3):
        # Враг получает еще столько же урона (двойной урон)
        monster.current_hp -= damage 
        return "БЕРСЕРК! Урон удвоен!"
    return None

def effect_spices(hero, monster, damage):
    spices_damage=int(random.randint(monster.min_attack, monster.max_attack) * 0.15)
    monster.current_hp -= spices_damage
    return f"Урон шипами +{spices_damage}"

def effect_atronach(hero, monster, damage):
    if hero.mp < hero.max_mp:
        hero.mp += 1
    return f"Востановлено 1 MP"

def effect_midas(hero, monster, damage):
    hero.gold += 1
    return f"Дает 1 золота"

def effect_damage_5(hero, monster, damage):
    damage = 5
    monster.current_hp -= damage 

def effect_mad_crown(hero, monster, damage):
    monster.current_hp -= damage 
    hero.hp -= 10
    return f"Урон удвоен! Корона отнимает -10HP"





# Реестр: связываем строку из БД с функцией
BATTLE_EFFECTS = {
    "vampirism_15": effect_vampirism,
    "berserk_low_hp": effect_berserk,
    "spices_15":effect_spices,
    "atronach":effect_atronach,
    "midas":effect_midas,
    "damage_5":effect_damage_5,
    "mad_crown":effect_mad_crown

}