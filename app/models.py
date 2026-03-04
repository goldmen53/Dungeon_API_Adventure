from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import random



class HeroArtifactLink(SQLModel, table=True):
    hero_id: Optional[int] = Field(default=None, foreign_key="hero.id", primary_key=True)
    artifact_id: Optional[int] = Field(default=None, foreign_key="artifact.id", primary_key=True)

class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    effect_key: Optional[str] = Field(default=None, nullable=True)

    bonus_strength: int = Field(default=0)
    bonus_vitality: int = Field(default=0)
    bonus_intelligence: int = Field(default=0)
    bonus_agility: int = Field(default=0)
    bonus_dexterity: int = Field(default=0)


    heroes: List["Hero"] = Relationship(back_populates="artifacts", link_model=HeroArtifactLink)




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
    mp: int = 50
    max_mp: int = 50
    hp: int = 100
    
    @property
    def total_vitality(self) -> int:
        bonus = sum(art.bonus_vitality for art in self.artifacts)
        return self.vitality + bonus

    @property
    def max_hp(self) -> int:
        return 20 + (self.total_vitality * 10)
    
    @property
    def total_dexterity(self) -> int:
        # Суммируем базу + бонусы от всех артефактов в рюкзаке
        bonus = sum(art.bonus_dexterity for art in self.artifacts)
        return self.dexterity + bonus
    
    @property
    def total_intelligence(self) -> int:
        # Суммируем базу + бонусы от всех артефактов в рюкзаке
        bonus = sum(art.bonus_intelligence for art in self.artifacts)
        return self.intelligence + bonus
    
    @property
    def total_agility(self) -> int:
        # Суммируем базу + бонусы от всех артефактов в рюкзаке
        bonus = sum(art.bonus_agility for art in self.artifacts)
        return self.agility + bonus
    
    @property
    def total_strength(self) -> int:
        # Суммируем базу + бонусы от всех артефактов в рюкзаке
        bonus = sum(art.bonus_strength for art in self.artifacts)
        return self.strength + bonus



    level: int = 1
    xp: int = 0
    gold: int = 0
    stat_points: int = Field(default=5) # Даем 5 очков на старте

    artifacts: List[Artifact] = Relationship(back_populates="heroes", link_model=HeroArtifactLink)


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

