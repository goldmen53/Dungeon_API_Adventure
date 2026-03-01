import random

MONSTER_TEMPLATES = {
    "rat": {
        "name": "Чумная крыса",
        "base_hp": 30,
        "base_attack": (2, 5),
        "base_gold": (1, 5),
        "base_xp": 15
    },
    "goblin": {
        "name": "Гоблин",
        "base_hp": 50,
        "base_attack": (5, 10),
        "base_gold": (5, 15),
        "base_xp": 30
    },
    "skeleton": {
        "name": "Скелет",
        "base_hp": 40,
        "base_attack": (8, 12),
        "base_gold": (0, 10),
        "base_xp": 40
    }
}

def create_monster_params(floor: int, is_boss: bool = False):
    # 1. Выбор шаблона
    if is_boss:
        # Для босса можно сделать отдельную логику, пока возьмем усиленного гоблина
        template = MONSTER_TEMPLATES["goblin"]
        name_prefix = "БОСС: "
        scale = 3.0 # Босс в 3 раза сильнее обычного моба на этаже
    else:
        template = random.choice(list(MONSTER_TEMPLATES.values()))
        name_prefix = ""
        scale = 1.0

    # 2. Масштабирование от этажа (скейлинг)
    # Каждые 10 этажей мобы становятся в 2 раза сильнее
    if floor < 10 :
        level_factor = 1 *scale
    else: 
        level_factor = 1 + (floor //10) * scale

    hp = int(template["base_hp"] * level_factor)
    min_atk = int(template["base_attack"][0] * level_factor)
    max_atk = int(template["base_attack"][1] * level_factor)
    
    # Награды тоже растут
    xp = int(template["base_xp"] * level_factor)
    min_g = int(template["base_gold"][0] * level_factor)
    max_g = int(template["base_gold"][1] * level_factor)

    return {
        "name": f"{name_prefix}{template['name']}",
        "level": level_factor,
        "max_hp": hp,
        "current_hp": hp,
        "min_attack": min_atk,
        "max_attack": max_atk,
        "min_gold": min_g,
        "max_gold": max_g,
        "xp_reward": xp
    }