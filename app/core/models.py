"""Data shapes for scraped articles and stored summaries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class ScrapedArticle(BaseModel):
    """Matches entries in article JSON feeds."""

    name: str
    published_relative: str = ""
    timestamp: str = ""
    link: str
    full_content: str
    source: str = ""


class ArticleSummary(BaseModel):
    """One row worth of data after LLM + before DB/email."""

    name: str
    link: str
    timestamp: str = ""
    source: str = ""
    summary: str
    processed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    llm_model: str = ""
    error: Optional[str] = None
