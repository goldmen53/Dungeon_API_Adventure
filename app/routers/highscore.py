from fastapi import APIRouter, Depends
from sqlmodel import Session, select, desc
from app.database import get_session
from app.models import HighScore
from typing import List

router = APIRouter(
    prefix="/highscore",
    tags=["HighScore"]
)

@router.get("/", response_model=List[HighScore])
def get_highscores(limit: int = 10, session: Session = Depends(get_session)):
    statement = select(HighScore).order_by(desc(HighScore.floor), desc(HighScore.level)).limit(limit)
    return session.exec(statement).all()
