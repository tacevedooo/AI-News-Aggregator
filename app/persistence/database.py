"""SQLite persistence for summarized articles."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from app.core.models import ArticleSummary


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS article_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                timestamp TEXT,
                source TEXT,
                summary TEXT NOT NULL,
                llm_model TEXT,
                error TEXT,
                processed_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def upsert_summaries(db_path: Path, rows: Iterable[ArticleSummary]) -> int:
    """Insert or replace by link. Returns number of rows written."""
    init_db(db_path)
    count = 0
    with _connect(db_path) as conn:
        for row in rows:
            conn.execute(
                """
                INSERT INTO article_summaries (
                    link, name, timestamp, source, summary, llm_model, error, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    name = excluded.name,
                    timestamp = excluded.timestamp,
                    source = excluded.source,
                    summary = excluded.summary,
                    llm_model = excluded.llm_model,
                    error = excluded.error,
                    processed_at = excluded.processed_at
                """,
                (
                    row.link,
                    row.name,
                    row.timestamp,
                    row.source,
                    row.summary,
                    row.llm_model,
                    row.error,
                    row.processed_at,
                ),
            )
            count += 1
        conn.commit()
    return count


def fetch_recent_summaries(db_path: Path, limit: int = 50) -> list[ArticleSummary]:
    init_db(db_path)
    out: list[ArticleSummary] = []
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT name, link, timestamp, source, summary, processed_at, llm_model, error
            FROM article_summaries
            ORDER BY processed_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        for name, link, ts, source, summary, processed_at, llm_model, error in cur.fetchall():
            out.append(
                ArticleSummary(
                    name=name,
                    link=link,
                    timestamp=ts or "",
                    source=source or "",
                    summary=summary or "",
                    processed_at=processed_at or "",
                    llm_model=llm_model or "",
                    error=error,
                )
            )
    return out
