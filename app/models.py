from sqlmodel import SQLModel, Field, Relationship,Column,JSON
from typing import Optional, List,Dict
import random
from pydantic import BaseModel
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    username : str = Field(index=True, unique=True)
    hashed_password : str


class LootChoice(BaseModel):
    type: str          # "artifact" или "spell"
    id: int
    name: str
    description: Optional[str] = None

class HeroArtifactLink(SQLModel, table=True):
    hero_id: Optional[int] = Field(default=None, foreign_key="hero.id", primary_key=True)
    artifact_id: Optional[int] = Field(default=None, foreign_key="artifact.id", primary_key=True)

class HeroSpellLink(SQLModel, table=True):
    hero_id: Optional[int] = Field(default=None, foreign_key="hero.id", primary_key=True)
    spell_id: Optional[int] = Field(default=None, foreign_key="spell.id", primary_key=True)

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
    max_mp: int = Field(default=0)
    bonus_flee: int = Field(default=0)
    bonus_crit: int = Field(default=0)
    level: int = Field(default=1)
    cost: int = Field(default=1)
    rarity: str = Field(default="base") # base,rare,epic,boss,store


    heroes: List["Hero"] = Relationship(back_populates="artifacts", link_model=HeroArtifactLink)




# --- БАЗОВЫЙ КЛАСС  ---
class Hero(SQLModel, table=True):
    # Первичный ключ 
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    name: str = Field(index=True, unique=True)
    

    # Характеристики
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    agility: int = 10
    vitality: int = 10
    mp: int = 50
    max_mp: int = 50
    hp: int = 200
    bonus_flee: int = 0
    bonus_crit: int = 0
    
    
    @property
    def total_vitality(self) -> int:
        bonus = sum(art.bonus_vitality for art in self.artifacts)
        return self.vitality + bonus

    @property
    def max_hp(self) -> int:
        return 100 + (self.total_vitality * 10)
    
    @property
    def total_flee(self) -> int:
        bonus = sum(art.bonus_flee for art in self.artifacts)
        return (self.total_agility + bonus)
    
    @property
    def total_crit(self) -> int:
        bonus = sum(art.bonus_crit for art in self.artifacts)
        return (self.total_dexterity + bonus)
    
    @property
    def total_dexterity(self) -> int:
        # Суммируем базу + бонусы от всех артефактов в рюкзаке
        bonus = sum(art.bonus_dexterity for art in self.artifacts)
        return self.dexterity + bonus
    
    @property
    def total_intelligence(self) -> int:
        bonus = sum(art.bonus_intelligence for art in self.artifacts)
        return self.intelligence + bonus
    
    @property
    def total_agility(self) -> int:
        bonus = sum(art.bonus_agility for art in self.artifacts)
        return self.agility + bonus
    
    @property
    def total_strength(self) -> int:
        bonus = sum(art.bonus_strength for art in self.artifacts)
        return self.strength + bonus



    level: int = 1
    xp: int = 0
    gold: int = 0
    stat_points: int = Field(default=5) # Даем 5 очков на старте

    artifacts: List["Artifact"] = Relationship(back_populates="heroes", link_model=HeroArtifactLink)
    spells: List["Spell"] = Relationship(back_populates="heroes", link_model=HeroSpellLink)
    
    # Храним ID артефактов в магазине как строку, разделенную запятыми
    current_shop_items: Optional[str] = Field(default=None)
    active_event_id: Optional[int] = Field(default=None, nullable=True)
    fights_without_drop: int = Field(default=0) 
    pending_loot: List[Dict] = Field(default_factory=list, sa_column=Column(JSON))


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
    flee: Optional[int] = Field(default=10)
    # Диапазоны для монстров
    min_attack: int = Field(default=5)
    max_attack: int = Field(default=10)
    min_gold: int = Field(default=1)
    max_gold: int = Field(default=10)
    xp_reward: int = Field(default=20) 



class HeroUpdate(SQLModel):
    strength: Optional[int] = None
    vitality: Optional[int] = None
    dexterity: Optional[int] = None
    intelligence: Optional[int] = None
    agility: Optional[int] = None
    hp: Optional[int] = None
    gold: Optional[int] = None
    xp: Optional[int] = None
    level: Optional[int] = None
    max_hp: Optional[int] = None
    max_mp: Optional[int] = None
    mp: Optional[int] = None
    stat_points: Optional[int] = None
    active_event_id: Optional[int] = None
    world_seed: Optional[int] = None
    current_room: Optional[int] = None
    current_lane: Optional[int] = None
    active_monster_id: Optional[int] = None
    bonus_flee: Optional[int] = None
    total_flee: Optional[int] = None
    bonus_crit: Optional[int] = None
    total_crit: Optional[int] = None


class MonsterUpdate(SQLModel):
    level: Optional[int] = None
    max_hp: Optional[int] = None
    current_hp: Optional[int] = None
    min_attack: Optional[int] = None
    max_attack: Optional[int] = None
    min_gold: Optional[int] = None
    max_gold: Optional[int] = None
    xp_reward: Optional[int] = None


class ArtifactRead(BaseModel):
    name: str
    description: str
    bonus_strength: int
    bonus_vitality: int
    bonus_intelligence: int
    bonus_agility: int
    bonus_dexterity: int
    bonus_flee: int
    bonus_crit: int
    level: int
    cost: int 
    rarity: str # base,rare,epic,boss,store
    max_mp: int 
    


class SpellRead(BaseModel):
    id : int
    name: str
    description: str
    level: int
    mp_cost: int 
    rarity: str # base,rare,epic,boss,store
    effect_key : str 
    price : int   

class HeroRead(BaseModel):
    id: int
    name: str
    hp: int
    max_hp: int
    mp: int
    max_mp : int
    stat_points: int
    xp:int
    total_strength: int
    total_dexterity: int
    total_intelligence: int
    total_agility: int
    total_vitality: int
    strength: int
    dexterity: int
    intelligence: int
    agility: int
    vitality: int
    level: int
    gold: int
    artifacts: List[ArtifactRead] = []
    bonus_flee: int
    total_flee: int
    bonus_crit: int
    total_crit: int
    spells: List[SpellRead] = []
    pending_loot: List[LootChoice] = []
    active_monster_id: Optional[int] = None
    class Config:
        from_attributes = True
    current_room: int
    current_lane: int



class Encounters(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    effect_key: str
    rarity: str = Field(default='base') 

    # --- Вариант 1 (ОБЯЗАТЕЛЬНЫЙ) ---
    choice_1_text: str  # Текст на кнопке (например, "Молиться о силе")
    choice_1_val: str   # Значение для бэкенда (например, "str")

    # --- ОПЦИОНАЛЬНЫЕ ВАРИАНТЫ ---
    choice_2_text: Optional[str] = Field(default=None)
    choice_2_val: Optional[str] = Field(default=None)

    choice_3_text: Optional[str] = Field(default=None)
    choice_3_val: Optional[str] = Field(default=None)

    choice_4_text: Optional[str] = Field(default=None)
    choice_4_val: Optional[str] = Field(default=None)

    choice_5_text: Optional[str] = Field(default=None)
    choice_5_val: Optional[str] = Field(default=None)


class Spell(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str 
    price : int = Field(default=10)
    description: str
    effect_key: Optional[str] = Field(default=None, nullable=True)
    mp_cost : int = Field(default=1)
    level: int = Field(default=1)
    rarity: str = Field(default="base") # base,rare,epic,boss,store
    heroes: List["Hero"] = Relationship(back_populates="spells", link_model=HeroSpellLink)
    
