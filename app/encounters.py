
PRESET_ENCOUNTERS = [

{
        "name": "Encounter with Wizard",
        "description": "Wizard offers to increase any stat of your choice",
        "effect_key": "give_any_stat",
        "rarity": "base",
        "choice_1_text": "Request str",
        "choice_1_val": "str",
        "choice_2_text": "Request agi",
        "choice_2_val": "agi",
        "choice_3_text": "Request dex",
        "choice_3_val": "dex",
        "choice_4_text": "Request int",
        "choice_4_val": "int",
        "choice_5_text": "Request vit",
        "choice_5_val": "vit"
},

{
        "name": "Altar of Forgotten God",
        "description": "Before you stands a pulsing blood monument. It whispers it will take your life force in exchange for fury 'sacrifice' -30hp",
        "effect_key": "altar_event",
        "rarity": "base",
        "choice_1_text": "Make sacrifice",
        "choice_1_val": "sacrifice",
        "choice_2_text": "Pray",
        "choice_2_val": "pray"
},

{
        "name": "Mysterious Goblin Gambler",
        "description": "Goblin tosses a gold coin. 'Want to play? Guess the side right — I'll double your bet. No — I'll take your purse! You can walk past'",
        "effect_key": "goblin_event",
        "rarity": "base",
        "choice_1_text": "Play",
        "choice_1_val": "play",
        "choice_2_text": "Walk away",
        "choice_2_val": "go_away"
},

{
        "name": "Abandoned Library",
        "description": "In a dusty hall lie two scrolls. One on a high shelf, the other protected by a magic barrier.",
        "effect_key": "library_event",
        "rarity": "base",
        "choice_1_text": "Reach for high shelf",
        "choice_1_val": "reach",
        "choice_2_text": "Focus on magic barrier",
        "choice_2_val": "decode"
},

{
        "name": "Strange Mirror",
        "description": "In another tunnel you see a strange mirror on the wall, it seems like there's something behind it",
        "effect_key": "mirror_event",
        "rarity": "base",
        "choice_1_text": "Look into your reflection",
        "choice_1_val": "look_closer",
        "choice_2_text": "Smash the mirror",
        "choice_2_val": "crash_mirror",
        "choice_3_text": "Walk past",
        "choice_3_val": "go_forward"
},

{
        "name": "Mushroom Glade",
        "description": "You stumbled upon a mushroom glade. The mushrooms look quite edible",
        "effect_key": "mushroom_event",
        "rarity": "base",
        "choice_1_text": "Eat red mushroom",
        "choice_1_val": "eat_red",
        "choice_2_text": "Eat blue mushroom",
        "choice_2_val": "eat_blue",
        "choice_3_text": "Trample mushrooms",
        "choice_3_val": "trample_mushrooms",
        "choice_4_text": "Walk past",
        "choice_4_val": "go_forward"
},

{
        "name": "Wishing Well",
        "description": "You see a strange brick structure in the middle of the dungeon, approaching you realize it's a well",
        "effect_key": "wishing_well_event",
        "rarity": "base",
        "choice_1_text": "Throw coin in well (-10 gold)",
        "choice_1_val": "toss_coin",
        "choice_2_text": "Throw rock in well",
        "choice_2_val": "toss_rock",
        "choice_3_text": "Spit in well",
        "choice_3_val": "spit",
        "choice_4_text": "Try to see something in the depths",
        "choice_4_val": "look_inside"
},
{
        "name": "Mysterious Cocoon",
        "description": "Hanging from the ceiling is a huge sticky cocoon. Inside you can see the outline of a human figure.",
        "effect_key": "cocoon_event",
        "rarity": "base",
        "choice_1_text": "Cut open cocoon",
        "choice_1_val": "cut",
        "choice_2_text": "Ignore",
        "choice_2_val": "ignore",
},

{
        "name": "Locked Chest",
        "description": "A normal chest, but it smells of burning.",
        "effect_key": "burnt_chest_event",
        "rarity": "base",
        "choice_1_text": "Open by force",
        "choice_1_val": "open_str",
        "choice_2_text": "Try to pick the lock",
        "choice_2_val": "open_agi",
        "choice_3_text": "Ignore",
        "choice_3_val": "ignore",
},

{
        "name": "Wandering Cook",
        "description": "A fat goblin is cooking stew right in the middle of the dungeon and offers you to try it! Just for 1 gold.",
        "effect_key": "cook_event",
        "rarity": "base",
        "choice_1_text": "Try (-1 gold)",
        "choice_1_val": "try",
        "choice_2_text": "Ignore the goblin",
        "choice_2_val": "ignore",
}

]