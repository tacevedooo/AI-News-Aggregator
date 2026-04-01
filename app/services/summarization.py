"""Summarize articles using a configurable LLM (free-tier friendly)."""

from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from app.core.models import ArticleSummary, ScrapedArticle

MAX_CONTENT_CHARS = 18_000

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_OLLAMA_BASE = "http://localhost:11434/v1"
DEFAULT_OLLAMA_MODEL = "llama3.2"


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 20] + "\n\n[... truncated ...]"


def _prompts(article: ScrapedArticle) -> tuple[str, str]:
    body = _truncate(article.full_content, MAX_CONTENT_CHARS)
    system = (
        "You are a concise tech news editor. Summarize articles for a daily digest. "
        "Use clear prose: 2–4 short paragraphs OR bullet points. "
        "No preamble, no 'In this article…'. Focus on facts, outcomes, and who it helps."
    )
    user = (
        f"Title: {article.name}\n"
        f"Source: {article.source}\n"
        f"URL: {article.link}\n\n"
        f"Article text:\n{body}"
    )
    return system, user


def _summarize_openai_compatible(
    article: ScrapedArticle,
    *,
    api_key: str,
    base_url: str | None,
    model: str,
) -> ArticleSummary:
    system, user = _prompts(article)
    try:
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = OpenAI(**kwargs)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=900,
        )
        text = (resp.choices[0].message.content or "").strip()
        return ArticleSummary(
            name=article.name,
            link=article.link,
            timestamp=article.timestamp,
            source=article.source,
            summary=text,
            llm_model=model,
        )
    except Exception as e:  # noqa: BLE001
        return ArticleSummary(
            name=article.name,
            link=article.link,
            timestamp=article.timestamp,
            source=article.source,
            summary="",
            llm_model=model,
            error=str(e),
        )


def _summarize_gemini(article: ScrapedArticle, *, api_key: str, model: str) -> ArticleSummary:
    import google.generativeai as genai

    system, user = _prompts(article)
    try:
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(
            model_name=model,
            system_instruction=system,
        )
        resp = m.generate_content(user)
        text = (resp.text or "").strip()
        return ArticleSummary(
            name=article.name,
            link=article.link,
            timestamp=article.timestamp,
            source=article.source,
            summary=text,
            llm_model=model,
        )
    except Exception as e:  # noqa: BLE001
        return ArticleSummary(
            name=article.name,
            link=article.link,
            timestamp=article.timestamp,
            source=article.source,
            summary="",
            llm_model=model,
            error=str(e),
        )


def summarize_article(
    article: ScrapedArticle,
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ArticleSummary:
    """
    LLM_PROVIDER (default: groq):
      - groq — free tier at console.groq.com; set GROQ_API_KEY
      - gemini — Google AI Studio free tier; set GEMINI_API_KEY
      - ollama — local; no key; OLLAMA_BASE_URL + OLLAMA_MODEL
      - openai — paid OpenAI; OPENAI_API_KEY (+ optional OPENAI_BASE_URL)
    """
    provider = (os.getenv("LLM_PROVIDER", "groq") or "groq").strip().lower()

    if provider == "gemini":
        key = (api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        m = (model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)).strip()
        if not key:
            return ArticleSummary(
                name=article.name,
                link=article.link,
                timestamp=article.timestamp,
                source=article.source,
                summary="",
                llm_model=m,
                error="Missing GEMINI_API_KEY (get a free key at https://aistudio.google.com/apikey)",
            )
        return _summarize_gemini(article, api_key=key, model=m)

    if provider == "ollama":
        m = (model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)).strip()
        url = (base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE)).strip()
        return _summarize_openai_compatible(
            article,
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            base_url=url,
            model=m,
        )

    if provider == "openai":
        key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        m = (model or os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")).strip()
        bu = (base_url or os.getenv("OPENAI_BASE_URL") or "").strip() or None
        if not key:
            return ArticleSummary(
                name=article.name,
                link=article.link,
                timestamp=article.timestamp,
                source=article.source,
                summary="",
                llm_model=m,
                error="Missing OPENAI_API_KEY",
            )
        return _summarize_openai_compatible(article, api_key=key, base_url=bu, model=m)

    # default: groq (free OpenAI-compatible API)
    key = (api_key or os.getenv("GROQ_API_KEY", "")).strip()
    m = (model or os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)).strip()
    if not key:
        return ArticleSummary(
            name=article.name,
            link=article.link,
            timestamp=article.timestamp,
            source=article.source,
            summary="",
            llm_model=m,
            error=(
                "Missing GROQ_API_KEY — create a free key at https://console.groq.com "
                "or set LLM_PROVIDER=gemini with GEMINI_API_KEY, or LLM_PROVIDER=ollama for local."
            ),
        )
    return _summarize_openai_compatible(
        article,
        api_key=key,
        base_url=GROQ_BASE_URL,
        model=m,
    )
