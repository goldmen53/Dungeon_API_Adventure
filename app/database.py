from sqlmodel import create_engine, Session, SQLModel
from typing import Generator

DATABASE_URL = "postgresql://player:quest@localhost:5432/dungeon_crawler"
 
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Creates tables in the database based on SQLModel classes."""
    SQLModel.metadata.create_all(engine)
    

def get_session() -> Generator[Session, None, None]:
    """Generator function to get DB session in FastAPI endpoints."""
    with Session(engine) as session:
        yield session