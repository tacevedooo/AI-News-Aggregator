"""End-to-end: JSON articles → LLM summaries → SQLite → optional email."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.config import load_env
from app.database import upsert_summaries
from app.email_digest import send_digest_email
from app.models import ScrapedArticle
from app.summarize import summarize_article


def load_articles_json(path: Path) -> list[ScrapedArticle]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON root must be a list of articles")
    return [ScrapedArticle.model_validate(item) for item in data]


def run_pipeline(
    json_path: Path,
    db_path: Path,
    *,
    send_email: bool = True,
) -> list:
    load_env()
    articles = load_articles_json(json_path)
    summaries = []
    for art in articles:
        summaries.append(summarize_article(art))

    written = upsert_summaries(db_path, summaries)
    print(f"Saved {written} row(s) to {db_path}")

    if send_email and os.getenv("SKIP_EMAIL", "").lower() not in ("1", "true", "yes"):
        try:
            send_digest_email(summaries)
            print("Digest email sent.")
        except RuntimeError as e:
            print(f"Email skipped: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"Email failed: {e}")

    for s in summaries:
        if s.error:
            print(f"[warn] {s.name}: {s.error}")
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize articles JSON, save to DB, email digest.")
    parser.add_argument(
        "json_path",
        nargs="?",
        default="recent_full_articles.json",
        help="Path to articles JSON (default: recent_full_articles.json)",
    )
    parser.add_argument(
        "--db",
        default="data/summaries.db",
        help="SQLite database path (default: data/summaries.db)",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Do not send email after processing",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    json_path = Path(args.json_path)
    if not json_path.is_absolute():
        json_path = root / json_path
    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = root / db_path

    run_pipeline(json_path, db_path, send_email=not args.no_email)


if __name__ == "__main__":
    main()
