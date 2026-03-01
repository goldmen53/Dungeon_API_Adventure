from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import random

# --- БАЗОВЫЙ КЛАСС (Общие поля для всех) ---
class Hero(SQLModel, table=True):
    # Первичный ключ (обязательно для table=True)
    id: Optional[int] = Field(default=None, primary_key=True)
    
    name: str = Field(index=True, unique=True)
    
    # Характеристики
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    agility: int = 10
    vitality: int = 10
    
    hp: int = 100
    max_hp: int = 100
    
    level: int = 1
    xp: int = 0
    gold: int = 0

    # Поля для генерации карты
    # По умолчанию создаем случайный сид при рождении героя
    world_seed: int = Field(default_factory=lambda: random.randint(1, 999999))
    current_room: int = 0  # Этаж (F0, F1...)
    current_lane: int = 1  # Дорожка (0, 1, 2)

    # ГЕОГРАФИЯ

    world_seed: int = Field(default_factory=lambda: random.randint(1, 999999))
    current_room: int = 0  # Этаж (F1, F2...)
    current_lane: int = 1  # Дорожка (0 - лево, 1 - центр, 2 - право)
    active_monster_id: Optional[int] = Field(default=None, nullable=True)

class Monster(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    level: int = Field(default=1)
    # Характеристики
    max_hp: int = Field(default=50)
    current_hp: int = Field(default=50)
    # Диапазоны (вместо фиксированных чисел)
    min_attack: int = Field(default=5)
    max_attack: int = Field(default=10)
    min_gold: int = Field(default=1)
    max_gold: int = Field(default=10)
    xp_reward: int = Field(default=20)  


class HeroUpdate(SQLModel):
    # Все поля Optional. Если мы их не прислали в JSON, они будут None
    strength: Optional[int] = None
    vitality: Optional[int] = None
    dexterity: Optional[int] = None
    intelligence: Optional[int] = None
    agility: Optional[int] = None
    current_hp: Optional[int] = None
    gold: Optional[int] = None
    xp: Optional[int] = None
    level: Optional[int] = None
    max_hp: Optional[int] = None
    max_mp: Optional[int] = None
    current_mp: Optional[int] = None

class MonsterUpdate(SQLModel):
    level: Optional[int] = None
    max_hp: Optional[int] = None
    current_hp: Optional[int] = None
    min_attack: Optional[int] = None
    max_attack: Optional[int] = None
    min_gold: Optional[int] = None
    max_gold: Optional[int] = None
    xp_reward: Optional[int] = None

