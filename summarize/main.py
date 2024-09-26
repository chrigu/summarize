from typing import Annotated
from uuid import UUID, uuid4

import uvicorn
import structlog
from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from markdown import markdown
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .crud import create_summaries, get_summary, get_summaries_without_podcast
from .database import SessionLocal, engine
from .extractor import make_summary, generate_and_save_audio
from .models import PodcastEpisode
from .podcast import combine_audio_files

logger = structlog.get_logger()

models.Base.metadata.create_all(bind=engine)
app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory="summarize/templates")
app.mount("/static", StaticFiles(directory="summarize/static"), name="static")


@app.get("/")
async def home(
    request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    summaries = crud.get_summaries(db, skip=skip, limit=limit)
    logger.debug(summaries)
    context = {"request": request, "summaries": summaries}
    return templates.TemplateResponse("summaries.html", context)


@app.get("/summaries/", response_model=list[schemas.Summary])
def read_summaries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    summaries = crud.get_summaries(db, skip=skip, limit=limit)
    return summaries


@app.get("/summaries/{summary_id}")
def read_summary(request: Request, summary_id: UUID, db: Session = Depends(get_db)):
    summary = get_summary(db, summary_id)
    context = {"request": request, "summary": summary, "summary_html_content": markdown(summary.content)}
    return templates.TemplateResponse("summary.html", context)

@app.post("/summaries/add-summary")
def add_summary(title: Annotated[str, Form()], url: Annotated[str, Form()], db: Session = Depends(get_db)):
    summary = schemas.SummaryCreate(title=title, web_url=url)
    db_summary = create_summaries(db, summary)
    rendered_li = templates.get_template("macros.html").module.list_summary(db_summary)
    return HTMLResponse(content=rendered_li)

@app.post("/summaries/summarize")
def summarize(summary_id: Annotated[UUID, Form()], db: Session = Depends(get_db)):
    summary = get_summary(db, summary_id)
    summary.content = make_summary(summary.web_url)
    summary.is_summarized = True
    db.commit()
    rendered_li = templates.get_template("macros.html").module.list_summary(summary)
    return HTMLResponse(content=rendered_li)


@app.post("/summaries/generate-audio")
def generate_audio(summary_id: Annotated[UUID, Form()], db: Session = Depends(get_db)):
    summary = get_summary(db, summary_id)
    generate_and_save_audio(summary.content, summary.id)
    summary.has_audio = True
    db.commit()

    rendered_li = templates.get_template("macros.html").module.list_summary(summary)
    return HTMLResponse(content=rendered_li)



@app.get("/podcasts", response_class=HTMLResponse)
async def get_podcasts(request: Request, db: Session = Depends(get_db)):
    # Query all podcasts from the database
    podcasts = db.query(PodcastEpisode).all()

    # Render the Jinja2 template with podcast data
    return templates.TemplateResponse("podcasts.html", {"request": request, "podcasts": podcasts})


@app.post("/podcasts/create-episode")
def create_podcast(db: Session = Depends(get_db)):
    # Query summaries that don't belong to any podcast episode
    summaries_without_podcast = get_summaries_without_podcast(db)

    # If no summaries found, return or handle accordingly
    if not summaries_without_podcast:
        return None

    new_podcast_filename = combine_audio_files(summaries_without_podcast)

    # Create a new PodcastEpisode entry
    new_podcast_episode = PodcastEpisode(
        id=uuid4(),
        title="Auto-generated Podcast Episode",
        audio_url=new_podcast_filename,
    )
    db.add(new_podcast_episode)
    db.commit()

    # Associate the summaries with the new podcast episode
    for summary in summaries_without_podcast:
        summary.podcast_episode_id = new_podcast_episode.id
        db.add(summary)

    # Commit the changes
    db.commit()

    return {"status": "success"}

def start():
    """Launched with `poetry run start` at root level"""
    uvicorn.run("summarize.main:app", host="0.0.0.0", port=8000, reload=True)
