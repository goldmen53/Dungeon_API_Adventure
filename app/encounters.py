

PRESET_ENCOUNTERS = [

{
        "name": "Вcтреча с волшебником",
        "description": "Волшебник предлогает увеличить любую характеристику на ваш выбор",
        "effect_key": "give_any_stat",
        "rarity": "base",
        "choice_1_text": "Попросить str",
        "choice_1_val": "str",
        "choice_2_text": "Попросить agi",
        "choice_2_val": "agi",
        "choice_3_text": "Попросить dex",
        "choice_3_val": "dex",
        "choice_4_text": "Попросить int",
        "choice_4_val": "int",
        "choice_5_text": "Попросить vit",
        "choice_5_val": "vit"
},

{
        "name": "Алтарь Забытого Бога",
        "description": "Перед вами пульсирующий кровавый монумент. Он шепчет, что заберет вашу жизненную силу в обмен на неистовство 'sacrifice' -30hp",
        "effect_key": "altar_event",
        "rarity": "base",
        "choice_1_text": "Принести жертву",
        "choice_1_val": "sacrifice",
        "choice_2_text": "Помолиться",
        "choice_2_val": "pray"
},

{
        "name": "Таинственный Гоблин-игрок",
        "description": "Гоблин подбрасывает золотую монету. 'Сыграем?  Угадаешь сторону — удвою ставку. Нет — заберу кошелек!Вы можете пройти мимо ",
        "effect_key": "goblin_event",
        "rarity": "base",
        "choice_1_text": "Сыграть",
        "choice_1_val": "play",
        "choice_2_text": "Уйти",
        "choice_2_val": "go_away"
},

{
        "name": "Заброшенная библиотека",
        "description": "В пыльном зале лежат два свитка. Один на высокой полке , другой защищен магическим барьером .",
        "effect_key": "library_event",
        "rarity": "base",
        "choice_1_text": "Потянуться к высокой полке",
        "choice_1_val": "reach",
        "choice_2_text": "Сосредоточиться на магическом барьере",
        "choice_2_val": "decode"
},

{
        "name": "Странное зеркало",
        "description": "В очередном тунеле на стене вы видите странное зеркало , вам кажеться что за ним что-то есть",
        "effect_key": "mirror_event",
        "rarity": "base",
        "choice_1_text": "Всмотреться в свое отражение",
        "choice_1_val": "look_closer",
        "choice_2_text": "Разбить зеркало",
        "choice_2_val": "crash_mirror",
        "choice_3_text": "Пройти мимо",
        "choice_3_val": "go_forward"
},

{
        "name": "Грибная поляна",
        "description": "Вы наткнулись на гибрную поляну.Грибы на ней вышлядят вполне съедобными ",
        "effect_key": "mushroom_event",
        "rarity": "base",
        "choice_1_text": "Сьесть красный гриб",
        "choice_1_val": "eat_red",
        "choice_2_text": "Сьесть синий гриб",
        "choice_2_val": "eat_blue",
        "choice_3_text": "Растоптать грибы",
        "choice_3_val": "trample_mushrooms",
        "choice_4_text": "Пройти мимо",
        "choice_4_val": "go_forward"
},

{
        "name": "Колодец желаний",
        "description": "Вы выидите стрнною кирпичную конструкцию посреди подземелья , подойдя по ближе вы понимаете, что это колодец",
        "effect_key": "wishing_well_event",
        "rarity": "base",
        "choice_1_text": "Кинуть монетку в колодец (-10 gold)",
        "choice_1_val": "toss_coin",
        "choice_2_text": "Кинуть камень в колодец",
        "choice_2_val": "toss_rock",
        "choice_3_text": "Плюнуть в колодец",
        "choice_3_val": "spit",
        "choice_4_text": "Попробовать разглядеть, что-то в глубине",
        "choice_4_val": "look_inside"
},
{
        "name": "Таинственный Кокон",
        "description": "На потолке висит огромный липкий кокон. Внутри видны очертания человеческой фигуры.",
        "effect_key": "cocoon_event",
        "rarity": "base",
        "choice_1_text": "Разрезать кокон",
        "choice_1_val": "cut",
        "choice_2_text": "Игнорировать",
        "choice_2_val": "ignore",
},

{
        "name": "Запертый Сундук",
        "description": "Обычный сундук, но от него пахнет гарью.",
        "effect_key": "burnt_chest_event",
        "rarity": "base",
        "choice_1_text": "Открыть силой",
        "choice_1_val": "open_str",
        "choice_2_text": "Попытаться вскрыть замок",
        "choice_2_val": "open_agi",
        "choice_3_text": "Проигнорировать",
        "choice_3_val": "ignore",
},

{
        "name": "Странствующий Повар",
        "description": "Толстый гоблин готовит рагу прямо посреди данжа и предлогает вам его попробовать! Всего за 1 золотой.",
        "effect_key": "сook_event",
        "rarity": "base",
        "choice_1_text": "Попробовать(-1 gold)",
        "choice_1_val": "try",
        "choice_2_text": "Проигнорировать гоблина",
        "choice_2_val": "ignore",
}

]