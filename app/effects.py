import random


def effect_vampirism(hero, monster, damage=0):
    heal = int(damage * 0.15)
    hero.hp = min(hero.max_hp, hero.hp + heal)
    return f"Vampirism: +{heal} HP"

def effect_berserk(hero, monster, damage=0):
    if hero.hp < (hero.max_hp * 0.3):
        # Enemy takes same damage again (double damage)
        monster.current_hp -= damage 
        return "BERSERK! Damage doubled!"
    return None

def effect_spikes(hero, monster, damage=0):
    spikes_damage=int(random.randint(monster.min_attack, monster.max_attack) * 0.15)
    monster.current_hp -= spikes_damage
    return f"Spike damage +{spikes_damage}"

def effect_atronach(hero, monster, damage=0):
    if hero.mp < hero.max_mp:
        hero.mp += 1
    return f"Restored 1 MP"

def effect_midas(hero, monster, damage=0):
    hero.gold += 1
    return f"Grants 1 gold"

def effect_damage_5(hero, monster, damage=0):
    damage = 5
    monster.current_hp -= damage 

def effect_mad_crown(hero, monster, damage=0):
    monster.current_hp -= damage 
    hero.hp -= 10
    return f"Damage doubled! Crown takes -10HP"




# Registry: link string from DB with function
BATTLE_EFFECTS = {
    "vampirism_15": effect_vampirism,
    "berserk_low_hp": effect_berserk,
    "spikes_15":effect_spikes,
    "atronach":effect_atronach,
    "midas":effect_midas,
    "damage_5":effect_damage_5,
    "mad_crown":effect_mad_crown

}