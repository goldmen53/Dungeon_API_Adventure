import random
from fastapi import FastAPI, Depends, HTTPException,Body,APIRouter
from app.database import init_db, get_session
from app.models import Hero,Artifact,HeroRead,Encounters,Spell,User
from sqlmodel import Session, select
from app.encounters_effects import ENCAUNTERS_EFFECTS
from app.utils import get_room_type
from app.auth_utils import get_current_hero




router = APIRouter(
    prefix="/world",
    tags=["World"]
)


@router.post("/rest") 
def hero_rest(hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    
    # DETERMINE CURRENT LOCATION TYPE
    # We use the same coordinates and seed as when moving
    current_room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)
    
    # Are we in a rest zone?
    if current_room_type != "R":
        raise HTTPException(
            status_code=400, 
            detail=f"It's dangerous here! You can't rest in a room of type '{current_room_type}'"
        )
    
    # CHECK GOLD AND HEALTH
    heal_cost = 5
    if hero.gold < heal_cost:
        raise HTTPException(status_code=400, detail="You need more gold for supplies!")
    
    if hero.hp == hero.max_hp:
        return {"message": "You are full of strength and don't need rest."}

    # APPLY EFFECTS
    hero.gold -= heal_cost
    hero.hp = hero.max_hp 
    
    # SAVE
    session.add(hero)
    session.commit()
    
    return {
        "message": "You set up camp and restored your strength.",
        "hp": f"{hero.hp}/{hero.max_hp}",
        "gold_left": hero.gold
    }

@router.get("/shop")
def get_shop_catalog(hero: Hero = Depends(get_current_hero),session: Session = Depends(get_session),):

    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    if hero.current_shop_items is None:
        statement = select(Artifact).where(Artifact.rarity.in_(["base", "store"]))
        all_available = session.exec(statement).all()
        
        count = min(3, len(all_available))
        selection = random.sample(all_available, k=count)
        
        # Save IDs
        hero.current_shop_items = ",".join([str(a.id) for a in selection])
        session.add(hero)
        session.commit()
    
    # If database has "empty" mark, everything was bought
    if hero.current_shop_items == "empty" or not hero.current_shop_items:
        return {"hero_gold": hero.gold, "items_for_sale": [], "message": "Shop is empty"}
    
    # Get artifact objects by saved IDs
    item_ids = [int(i) for i in hero.current_shop_items.split(",") if i]
    shop_items = session.exec(select(Artifact).where(Artifact.id.in_(item_ids))).all()

    return {
        "hero_gold": hero.gold,
        "items_for_sale": shop_items
    }

@router.post("/resolve_event")
def resolve_event(choice: str, hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    if not hero.active_event_id:
        raise HTTPException(status_code=400, detail="You have no active events")

    event = session.get(Encounters, hero.active_event_id)
    
    # 1. CHEATER PROTECTION: Check that sent choice actually exists in this event
    valid_choices = [
        event.choice_1_val, event.choice_2_val, event.choice_3_val, 
        event.choice_4_val, event.choice_5_val
    ]
    if choice not in valid_choices:
         raise HTTPException(status_code=400, detail="Invalid choice for this event")

    # 2. Call effect
    handler = ENCAUNTERS_EFFECTS.get(event.effect_key)
    if handler:
        message = handler(hero, session, choice)
        session.commit()
        return {"message": message, "hero": hero}
    
    raise HTTPException(status_code=500, detail="Event processing error: handler not found")

@router.post("/buy")
def buy_artifact( artifact_id: int, hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    artifact = session.get(Artifact, artifact_id)

    if not hero or not artifact:
        raise HTTPException(status_code=404, detail="Hero or artifact not found")

    current_room_type = get_room_type(hero.current_room, hero.current_lane, hero.world_seed)
    
    # Check location
    if current_room_type != "S":
        raise HTTPException(
            status_code=400, 
            detail=f"Artifacts can only be bought in a shop"
        )

    # Check money
    if hero.gold < artifact.cost:
        raise HTTPException(status_code=400, detail="Not enough gold!")

    # Check if artifact already exists
    if artifact in hero.artifacts:
        raise HTTPException(status_code=400, detail="You already have this artifact")

    # Check if this item is in current shop
    current_items = hero.current_shop_items.split(",")
    if str(artifact_id) not in current_items:
        raise HTTPException(status_code=400, detail="This item is no longer for sale")
    
   
    
    new_items = [i for i in current_items if i != str(artifact_id)]

    if len(new_items) == 0:
        hero.current_shop_items = "empty" # Mark shop as fully bought
    else:
        hero.current_shop_items = ",".join(new_items)


    # Make the deal
    hero.gold -= artifact.cost
    hero.artifacts.append(artifact)
    
    # Remove purchased ID from shop list
    current_items.remove(str(artifact_id))
    hero.current_shop_items = ",".join(current_items)

    session.add(hero)
    session.commit()
    
    return {"message": f"Purchased: {artifact.name}", "new_gold": hero.gold}

@router.post("/pick_loot")
def pick_loot(
    choice_type: str, # "artifact" or "spell"
    choice_id: int, 
    session: Session = Depends(get_session),
    hero: Hero = Depends(get_current_hero), 

):
    # Find hero
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    # Check if there's anything to choose from
    if not hero.pending_loot:
        raise HTTPException(status_code=400, detail="You have no pending rewards")

    # Validate choice: check if this item was in the offered list
    # pending_loot stores list of dicts: [{"type": "artifact", "id": 1, ...}, ...]
    is_valid_choice = any(
        item["type"] == choice_type and item["id"] == choice_id 
        for item in hero.pending_loot
    )
    
    if not is_valid_choice:
        raise HTTPException(status_code=400, detail="This item was not in your reward list")

    # Award the reward
    message = ""
    if choice_type == "artifact":
        artifact = session.get(Artifact, choice_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found in database")
        
        # Duplicate check (if artifacts are unique)
        if artifact in hero.artifacts:
            # If already owned, give gold compensation
            hero.gold += 20
            message = f"You already have {artifact.name}. You received 20 gold instead."
        else:
            hero.artifacts.append(artifact)
            message = f"You received artifact: {artifact.name}!"

    elif choice_type == "spell":
        spell = session.get(Spell, choice_id)
        if not spell:
            raise HTTPException(status_code=404, detail="Spell not found")
        
        if spell in hero.spells:
            hero.gold += 15
            message = f"You already know spell {spell.name}. Received 15 gold."
        else:
            hero.spells.append(spell)
            message = f"You learned new spell: {spell.name}!"
    else:
        raise HTTPException(status_code=400, detail="Invalid reward type")

    # Clear selection list so it can't be chosen again
    hero.pending_loot = []
    
    session.add(hero)
    session.commit()
    session.refresh(hero)

    return {
        "message": message,
        "hero_id": hero.id,
        "current_artifacts": [a.name for a in hero.artifacts],
        "current_spells": [s.name for s in hero.spells]
    }   

@router.get("/current_event")
def get_current_event(hero: Hero = Depends(get_current_hero), session: Session = Depends(get_session)):
    if not hero.active_event_id:
        raise HTTPException(status_code=400, detail="You have no active events")
        
    event = session.get(Encounters, hero.active_event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Build button array on the fly
    choices = [{"text": event.choice_1_text, "value": event.choice_1_val}]
    
    if event.choice_2_text and event.choice_2_val:
        choices.append({"text": event.choice_2_text, "value": event.choice_2_val})
    if event.choice_3_text and event.choice_3_val:
        choices.append({"text": event.choice_3_text, "value": event.choice_3_val})
    if event.choice_4_text and event.choice_4_val:
        choices.append({"text": event.choice_4_text, "value": event.choice_4_val})
    if event.choice_5_text and event.choice_5_val:
        choices.append({"text": event.choice_5_text, "value": event.choice_5_val})

    return {
        "name": event.name,
        "description": event.description,
        "choices": choices
    }