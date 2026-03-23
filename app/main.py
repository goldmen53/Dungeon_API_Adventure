# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from app.database import init_db, get_session
from app.models import Monster,Artifact,Spell,HighScore
from sqlmodel import Session, select
from fastapi.responses import FileResponse
from app.utils import init_artifacts,init_spells,init_encounters
from app.routers import auth, heroes, battle, world, admin, highscore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os




app = FastAPI(title="Dungeon_API_Adventure")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows requests from any origin (important for frontend)
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Allows any headers (including your Authorization)
)


script_dir = os.path.dirname(__file__)
static_path = os.path.join(script_dir, "../static") # path to static folder

app.mount("/static", StaticFiles(directory=static_path), name="static")

# Connect modules
app.include_router(auth.router)
app.include_router(heroes.router)
app.include_router(battle.router)
app.include_router(world.router)
app.include_router(admin.router)
app.include_router(highscore.router)


@app.get("/")
def read_index():
    # FastAPI just reads index.html and serves it to browser
    return FileResponse("static/index.html")

# Create tables on startup
@app.on_event("startup")
def on_startup():
    init_db()
    session_generator = get_session()
    session = next(session_generator)
    
    try:
        init_artifacts(session)
        init_encounters(session)
        init_spells(session)
    finally:
        session.close() # Always close session manually

@app.get("/")
def welcome():
    return {"message": "Dungeon awaits!"}

@app.get("/monsters/{name}")
def get_monster_status(name: str, session: Session = Depends(get_session)):
    # Select all from Monster table where name matches
    statement = select(Monster).where(Monster.name == name)
    
    # Execute query and get first result
    monster = session.exec(statement).first()
    
    # If monster not found
    if not monster:
        raise HTTPException(status_code=404, detail="Monster not found in this dungeon")
    
    return monster

@app.get('/monsters/')
def get_all_monsters(session: Session = Depends(get_session)):

    statement = select(Monster)

    monsters = session.exec(statement).all()

    if not monsters : 
        raise HTTPException(status_code=404, detail="No monsters in the dungeon")
    
    return monsters

@app.get("/artifacts/all")
def list_all_artifacts(session: Session = Depends(get_session)):
    artifacts = session.exec(select(Artifact)).all()
    return artifacts

@app.get("/spell/all")
def list_all_spell(session: Session = Depends(get_session)):
    spells = session.exec(select(Spell)).all()
    return spells