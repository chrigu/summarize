from sqlalchemy.orm import Session
from uuid import uuid4, UUID

from . import models, schemas


def get_summaries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Summary).offset(skip).limit(limit).all()


def get_summary(db: Session, summary_id: UUID):
    return db.get(models.Summary, summary_id)


def get_summaries_without_podcast(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Summary).filter(
        models.Summary.podcast_episode_id == None,
        models.Summary.has_audio == True).offset(skip).limit(limit).all()


def create_summaries(db: Session, summary: schemas.SummaryCreate):
    summary.id = uuid4()
    db_summary = models.Summary(**summary.dict())
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary
