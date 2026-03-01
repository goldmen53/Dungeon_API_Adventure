from sqlmodel import create_engine, Session, SQLModel
from typing import Generator

# Параметры подключения, которые мы задали в docker-compose.yml
# Схема: postgresql://user:password@host:port/database_name
DATABASE_URL = "postgresql://player:quest@localhost:5432/dungeon_crawler"

# echo=True заставит SQLAlchemy выводить в консоль все SQL-запросы. 
# Это ОЧЕНЬ круто для обучения, ты будешь видеть, как Python превращается в SQL.
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Создает таблицы в базе данных на основе моделей SQLModel."""
    # Важно: здесь SQLModel найдет все классы с table=True, 
    # которые были импортированы в проект на момент вызова.
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Функция-генератор для получения сессии БД в эндпоинтах FastAPI."""
    with Session(engine) as session:
        yield session