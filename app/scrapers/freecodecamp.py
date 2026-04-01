"""Scrape recent freeCodeCamp news articles into the data inbox JSON."""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = _REPO_ROOT / "data" / "inbox" / "recent_full_articles.json"


def get_full_article_content(article_url: str) -> str:
    """Visit the article page and extract text from main post content."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(article_url, headers=headers, timeout=10)
        article_soup = BeautifulSoup(response.text, "html.parser")

        content_section = article_soup.find(["section", "div"], class_="post-content")

        if content_section:
            paragraphs = content_section.find_all("p")
            return "\n\n".join([p.get_text(strip=True) for p in paragraphs])

        return "Content body could not be located on the page."
    except Exception as e:  # noqa: BLE001
        return f"Error downloading content: {e}"


def scrape_recent_freecodecamp(output_path: Path | None = None) -> None:
    """Scrape articles from roughly the last 24 hours and save JSON for the digest pipeline."""
    out = output_path or DEFAULT_OUTPUT
    out.parent.mkdir(parents=True, exist_ok=True)

    base_url = "https://www.freecodecamp.org/news/"
    headers = {"User-Agent": "Mozilla/5.0"}

    print("Fetching the main feed...")
    response = requests.get(base_url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    news_list: list[dict] = []
    articles = soup.find_all("article", class_="post-card")

    for post in articles:
        time_tag = post.find("time", class_="meta-item")

        if time_tag:
            time_text = time_tag.get_text(strip=True).lower()

            if "hour" in time_text or "minute" in time_text:
                title_element = post.find("h2", class_="post-card-title")
                link_tag = post.find("a", href=True)

                if title_element and link_tag:
                    full_link = "https://www.freecodecamp.org" + link_tag["href"]
                    article_name = title_element.get_text(strip=True)

                    print(f"Found Recent Article ({time_text}): {article_name}")
                    print("   --> Downloading full content...")

                    full_body = get_full_article_content(full_link)

                    news_list.append(
                        {
                            "name": article_name,
                            "published_relative": time_text,
                            "timestamp": time_tag.get("datetime"),
                            "link": full_link,
                            "full_content": full_body,
                            "source": "FreeCodeCamp",
                        }
                    )

                    time.sleep(1.5)

    if news_list:
        out.write_text(json.dumps(news_list, ensure_ascii=False, indent=4), encoding="utf-8")
        print(f"\nSuccess! Saved {len(news_list)} full articles to:\n  {out}")
    else:
        print("\nNo articles found from the last 24 hours.")


if __name__ == "__main__":
    scrape_recent_freecodecamp()
