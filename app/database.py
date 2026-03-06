from sqlmodel import create_engine, Session, SQLModel
from typing import Generator

DATABASE_URL = "postgresql://player:quest@localhost:5432/dungeon_crawler"
 
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Создает таблицы в базе данных на основе моделей SQLModel."""
    SQLModel.metadata.create_all(engine)
    

def get_session() -> Generator[Session, None, None]:
    """Функция-генератор для получения сессии БД в эндпоинтах FastAPI."""
    with Session(engine) as session:
        yield session