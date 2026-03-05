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






# Реестр: связываем строку из БД с функцией
BATTLE_EFFECTS = {
    "vampirism_15": effect_vampirism,
    "berserk_low_hp": effect_berserk
}