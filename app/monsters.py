import random

MONSTER_TEMPLATES = {
    "rat": {
        "name": "Plague Rat",
        "base_hp": 30,
        "base_attack": (2, 5),
        "base_gold": (1, 5),
        "base_xp": 20
    },
    "goblin": {
        "name": "Goblin",
        "base_hp": 50,
        "base_attack": (5, 10),
        "base_gold": (5, 15),
        "base_xp": 25
    },
    "skeleton": {
        "name": "Skeleton",
        "base_hp": 40,
        "base_attack": (8, 12),
        "base_gold": (0, 10),
        "base_xp": 30
    }
}

def create_monster_params(floor: int, is_boss: bool = False):
    # Template selection
    if is_boss:
        # For boss could make separate logic, for now take enhanced goblin
        template = MONSTER_TEMPLATES["goblin"]
        name_prefix = "BOSS: "
        scale = 2.0 # Boss is 2x stronger than regular mob on floor
    else:
        template = random.choice(list(MONSTER_TEMPLATES.values()))
        name_prefix = ""
        scale = 1.0

    # Mob scaling based on floor
    # Every 10 floors mobs become 2x stronger
    if floor < 10 :
        level_factor = 1 *scale
    else: 
        level_factor = 1 + (floor //10) * scale

    hp = int(template["base_hp"] * level_factor)
    min_atk = int(template["base_attack"][0] * level_factor)
    max_atk = int(template["base_attack"][1] * level_factor)
    
    # Reward scaling
    xp = int(template["base_xp"])
    min_g = int(template["base_gold"][0])
    max_g = int(template["base_gold"][1])

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