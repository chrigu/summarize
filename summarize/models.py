from sqlalchemy import Boolean, Column, String, UUID, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(UUID, primary_key=True)
    title = Column(String, index=True)
    web_url = Column(String, index=True)
    content = Column(String)
    audio_url = Column(String)
    file_name = Column(String)
    text = Column(String)
    is_summarized = Column(Boolean, default=False)
    has_audio = Column(Boolean, default=False)
    podcast_episode_id = Column(UUID, ForeignKey("podcast_episodes.id"))

    podcast_episode = relationship("PodcastEpisode", back_populates="summaries")


class PodcastEpisode(Base):
    __tablename__ = "podcast_episodes"

    id = Column(UUID, primary_key=True)
    title = Column(String, index=True)
    audio_url = Column(String)
    summaries = relationship("Summary", back_populates="podcast_episode")
