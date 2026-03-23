# Dungeon Crawler RPG

A full-stack dungeon crawler game built with **FastAPI** (backend) and **vanilla JavaScript** (frontend). Players explore procedurally generated dungeons, fight monsters, collect artifacts and spells, manage stats, and try to reach the deepest floor.

## Features

- **Procedural Dungeon Generation**: Each floor has random room layouts with 3 lanes (left, center, right)
- **Turn-Based Combat**: Combat system with attack, flee, and spell casting
- **Character Progression**: Level up, gain gold, spend stat points (Strength, Vitality, Agility, Dexterity, Intelligence)
- **Artifact System**: Equip weapons and armor with special effects (vampirism, berserk mode, spikes, etc.)
- **Spell System**: Learn and use spells in combat (heal, fireball, chain lightning, etc.)
- **Random Encounters**: Non-combat events with choices that affect your hero
- **Shop System**: Buy artifacts and spells between floors
- **High Score Board**: Tracks best runs - saved when hero dies
- **Authentication**: User registration and login system

## Tech Stack

- **Backend**: FastAPI, SQLModel, PostgreSQL
- **Frontend**: Vanilla HTML, CSS, JavaScript
- **Database**: PostgreSQL

## Project Structure

```
Dungeon_Crowler_game/
├── app/                      # Backend Python code
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # SQLModel database models
│   ├── database.py         # Database connection setup
│   ├── auth_utils.py       # Authentication utilities
│   ├── utils.py            # General utilities
│   ├── monsters.py         # Monster generation logic
│   ├── artifacts.py        # Artifact definitions
│   ├── spells.py           # Spell definitions
│   ├── effects.py         # Combat effect handlers
│   ├── spell_effects.py   # Spell effect handlers
│   ├── encounters.py      # Random encounter definitions
│   ├── encounters_effects.py # Encounter effect handlers
│   ├── routers/           # API route handlers
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── heroes.py      # Hero management endpoints
│   │   ├── battle.py      # Combat endpoints
│   │   ├── world.py       # Dungeon/room endpoints
│   │   ├── admin.py       # Admin endpoints
│   │   └── highscore.py  # High score endpoints
│   └── __init__.py
├── static/                  # Frontend static files
│   ├── index.html         # Main game UI
│   ├── game.js            # Game logic and API calls
│   └── style.css         # Styling
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
└── docker-compose.yml    # Docker Compose setup
```

## Installation

### Prerequisites

- Python 3.13+
- PostgreSQL database

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Dungeon_Crowler_game
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables for database connection (or use docker-compose).

### Running with Docker

```bash
docker-compose up --build
```

The game will be available at `http://localhost:8000`

### Running without Docker

1. Create a PostgreSQL database
2. Update database connection string in `app/database.py`
3. Run the server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Heroes
- `POST /heroes/create` - Create new hero
- `GET /heroes/me` - Get current hero
- `PUT /heroes/stats` - Allocate stat points
- `GET /heroes/shop` - Get shop items
- `POST /heroes/buy` - Buy artifact or spell

### Battle
- `POST /battle/start` - Start combat
- `POST /battle/attack` - Attack monster
- `POST /battle/flee` - Attempt to flee
- `POST /battle/cast` - Cast spell

### World
- `GET /world/room` - Get current room info
- `POST /world/move` - Move to another lane
- `POST /world/next` - Go to next floor

### High Scores
- `GET /highscore/` - Get top scores

## Gameplay

1. **Create an account** and log in
2. **Create a hero** with a custom name
3. **Explore the dungeon** - Choose left, center, or right lane
4. **Fight monsters** - Use attack, flee, or spells
5. **Collect loot** - Artifacts and spells drop from enemies
6. **Visit the shop** - Buy equipment between floors
7. **Level up** - Gain stat points and increase stats
8. **Reach deeper floors** - Try to get the highest score
9. **Game over** - Your run is saved to the high score board

## Stat System

- **Strength**: Increases physical damage
- **Vitality**: Increases max HP
- **Agility**: Increases flee chance
- **Dexterity**: Increases critical hit chance
- **Intelligence**: Required for certain spells (affects MP)

## License

MIT License