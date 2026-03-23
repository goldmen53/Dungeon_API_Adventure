import random
from fastapi import  Depends, HTTPException,Body,APIRouter
from app.database import  get_session
from app.models import Hero,  Monster, HeroRead,Encounters,User
from sqlmodel import Session, select
from app.monsters import create_monster_params
from app.auth_utils import get_current_hero,validate_hero_name,get_current_user



router = APIRouter(
    prefix="/heroes",
    tags=["Heroes"] # Grouping in Swagger
)

@router.post("/create")
def create_hero(name: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    
    lowered_name = name.lower()
    
    
    validate_hero_name(lowered_name)

    
    existing_name = session.exec(select(Hero).where(Hero.name == lowered_name)).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="This name is already taken")

    
    existing_hero = session.exec(select(Hero).where(Hero.user_id == current_user.id)).first()
    if existing_hero:
        raise HTTPException(status_code=400, detail="You already have an active hero")

    new_hero = Hero(name=lowered_name, user_id=current_user.id)
    session.add(new_hero)
    session.commit()
    session.refresh(new_hero)
    
    return {
        "message": f"Hero {new_hero.name.capitalize()} entered the dungeon!",
        "hero_id": new_hero.id
    }


@router.get("/me", response_model=HeroRead)
def get_my_hero(hero: Hero = Depends(get_current_hero)):
    if not hero:
        return None
    return hero

@router.post("/upgrade")
def upgrade_stat(stat: str,amount: int,hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    if hero.stat_points <= 0:
        raise HTTPException(status_code=400, detail="You have no available stat points")
    
    if amount > hero.stat_points:
        raise HTTPException(status_code=400, detail="Not enough stat points")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount cannot be negative or zero")
    

    if stat == "str" and (amount + hero.strength) <=50:
        hero.strength += amount
    elif stat == "agi" and (amount + hero.agility) <=50:
        hero.agility += amount
    
    elif stat == "vit" and (amount + hero.vitality) <=50:
        hero.vitality += amount
        # Immediately update max HP by formula
        hero.hp += (hero.vitality*10)
        if hero.hp > hero.max_hp:
            hero.hp = hero.max_hp

    elif stat == "int" and (amount + hero.intelligence) <=50:
        hero.intelligence += amount
    elif stat == "dex" and (amount + hero.dexterity) <=50:
        hero.dexterity += amount

    else:
        raise HTTPException(status_code=400, detail="Invalid stat or stat > 50")
    
    hero.stat_points -= amount

    session.add(hero)
    session.commit()
    session.refresh(hero)
    
    return {
        "message": f"{stat} successfully increased!",
        "current_stats": {
            "str": hero.strength,
            "agi": hero.agility,
            "vit": hero.vitality,
            "int": hero.intelligence,
            "dex": hero.dexterity,
            "points_left": hero.stat_points
        }
    }

@router.post("/move")
def move_hero(target_lane: int,hero: Hero = Depends(get_current_hero),session: Session = Depends(get_session)):

    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    # First, BATTLE CHECK (cannot leave current room if there's an enemy)
    if hero.active_monster_id:
        monster = session.get(Monster, hero.active_monster_id)
        if monster and monster.current_hp > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"You cannot leave while {monster.name} is alive!"
            )

    # LANE CHECK (can only move to adjacent lanes)
    allowed_lanes = [hero.current_lane, hero.current_lane - 1, hero.current_lane + 1]
    if target_lane not in allowed_lanes or target_lane not in [0, 1, 2]:
         raise HTTPException(status_code=400, detail="Invalid move")

    # STEP FORWARD (Change coordinates BEFORE generating room type)
    hero.current_room += 1
    hero.current_lane = target_lane
    
    # DETERMINE NEW ROOM TYPE
    room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)

    # SPAWN LOGIC
    m_params = None
    if room_type == "B" or room_type == "BOSS":
        m_params = create_monster_params(hero.current_room, is_boss=(room_type == "BOSS"))
        new_monster = Monster(**m_params)
        session.add(new_monster)
        session.flush() 
        hero.active_monster_id = new_monster.id
    else:
        hero.active_monster_id = None

    if room_type == "E":
        all_events = session.exec(select(Encounters)).all()
        if not all_events:
            hero.gold += 10
            return {"message": "There should be an event here, but the world is empty. You found 10 gold."}

        selected_event = random.choice(all_events)
        
        # Lock the hero
        hero.active_event_id = selected_event.id
        session.add(hero)
        session.commit()
        
        # --- BUILD BUTTON ARRAY FOR FRONTEND ---
        choices = []
        # Option 1 always exists
        choices.append({"text": selected_event.choice_1_text, "value": selected_event.choice_1_val})
        
        # Check optional ones
        if selected_event.choice_2_text and selected_event.choice_2_val:
            choices.append({"text": selected_event.choice_2_text, "value": selected_event.choice_2_val})
        if selected_event.choice_3_text and selected_event.choice_3_val:
            choices.append({"text": selected_event.choice_3_text, "value": selected_event.choice_3_val})
        if selected_event.choice_4_text and selected_event.choice_4_val:
            choices.append({"text": selected_event.choice_4_text, "value": selected_event.choice_4_val})
        if selected_event.choice_5_text and selected_event.choice_5_val:
            choices.append({"text": selected_event.choice_5_text, "value": selected_event.choice_5_val})

        return {
            "type": "event",
            "event_name": selected_event.name,
            "description": selected_event.description,
            "choices": choices
        }


    #Shop update logic. Reset shop and regenerate on each step
    hero.current_shop_items = None

    session.add(hero)
    session.commit()
    session.refresh(hero)
    
    return {
        "event": "You encountered an enemy!" if hero.active_monster_id else "You entered a peaceful zone",
        "current_floor": hero.current_room,
        "room_type": room_type,
        "monster": m_params
    }

@router.get("/map")
def get_hero_map(hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):   
    
    visible_map = []
    # Show current floor
    if hero.current_room < 11:
        map = 0
    else:
        map = (hero.current_room //10 )*10
    # Unique spaghetti code for floor 0 rendering, maybe remove later
    if hero.current_room < 11:
        for f in range( map,map+11 ):
            floor_data = {
                "floor": f"F{f}",
                "lanes": {
                    "Left (0)": get_room_type(f, 0, hero.world_seed),
                    "Center (1)": get_room_type(f, 1, hero.world_seed),
                    "Right (2)": get_room_type(f, 2, hero.world_seed)
                },
                "is_current": f == hero.current_room
            }
            visible_map.append(floor_data)

    else:
        for f in range( map+1,map+11 ):
            floor_data = {
                "floor": f"F{f}",
                "lanes": {
                    "Left (0)": get_room_type(f, 0, hero.world_seed),
                    "Center (1)": get_room_type(f, 1, hero.world_seed),
                    "Right (2)": get_room_type(f, 2, hero.world_seed)
                },
                "is_current": f == hero.current_room
            }
            visible_map.append(floor_data)
        
    return {
    "hero_position": {
        "floor": hero.current_room, 
        "lane": hero.current_lane,
        "room_type": get_room_type(hero.current_room, hero.current_lane, hero.world_seed),
        "is_rest_zone": get_room_type(hero.current_room, hero.current_lane, hero.world_seed) == "R"
    },
    "map_preview": visible_map
}