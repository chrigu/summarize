from uuid import UUID

from pydantic import BaseModel


class SummaryBase(BaseModel):
    id: UUID | None = None
    title: str
    web_url: str | None = None
    text: str | None = None
    is_summarized: bool = False
    has_audio: bool = False


class SummaryCreate(SummaryBase):
    pass


class Summary(SummaryBase):
    id: UUID
    content: str
    audio_url: str | None = None

    class Config:
        from_attributes = True


class PodcastEpisodeBase(BaseModel):
    id: UUID | None = None
    title: str
    audio_url: str | None = None
    file_name: str | None = None
    

class PodcastEpisodeCreate(PodcastEpisodeBase):
    pass


class PodcastEpisode(PodcastEpisodeBase):
    id: UUID
    summaries: list[Summary] = []

    class Config:
        from_attributes = True
