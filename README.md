# AI News Aggregator

Collect recent developer news articles, summarize them with an LLM, store results in SQLite, and optionally email a digest.

## What it does

1. **Scrape** — Pull recent articles (e.g. from freeCodeCamp) into `recent_full_articles.json`.
2. **Summarize** — Read that JSON, call a configurable LLM per article, produce short digests.
3. **Persist** — Upsert summaries into a local SQLite database (`data/summaries.db` by default).
4. **Notify** — Send a multipart (plain + HTML) email with all summaries via SMTP (e.g. Gmail).

## Requirements

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** (recommended) or `pip`

## Setup

```bash
git clone <your-repo-url>
cd AI-News-Aggregator
uv sync
```

Copy environment variables into `app/.env` (or a `.env` at the repo root). Files matching `.env` are gitignored.

## Environment variables

### LLM (pick one provider)

| Variable | Purpose |
|----------|---------|
| `LLM_PROVIDER` | `groq` (default), `gemini`, `ollama`, or `openai` |

**Groq (default, free tier)** — [console.groq.com](https://console.groq.com)

- `GROQ_API_KEY` — required for default mode  
- `GROQ_MODEL` — optional, default `llama-3.3-70b-versatile`

**Google Gemini (free tier)** — [Google AI Studio](https://aistudio.google.com/apikey)

- `LLM_PROVIDER=gemini`
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`)
- `GEMINI_MODEL` — optional, default `gemini-1.5-flash`

**Ollama (local, no API bill)**

- `LLM_PROVIDER=ollama`
- `OLLAMA_BASE_URL` — optional, default `http://localhost:11434/v1`
- `OLLAMA_MODEL` — optional, default `llama3.2`

**OpenAI**

- `LLM_PROVIDER=openai`
- `OPENAI_API_KEY`
- `OPENAI_SUMMARY_MODEL` — optional (e.g. `gpt-4o-mini`)
- `OPENAI_BASE_URL` — optional (compatible proxies)

### Email (optional)

If SMTP is not configured, the pipeline still runs and saves to the database; email is skipped with a short message.

| Variable | Description |
|----------|-------------|
| `SMTP_HOST` | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | e.g. `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | Usually Gmail **App Password**, not your normal password |
| `EMAIL_FROM` | Sender address (often same as `SMTP_USER`) |
| `EMAIL_TO` | Comma-separated recipients |
| `SMTP_USE_TLS` | `true` for port 587 (default) |
| `SMTP_USE_SSL` | `true` for port 465 |
| `EMAIL_SUBJECT` | Optional subject line |
| `SKIP_EMAIL` | Set to `true` to never send |

### Other

| Variable | Description |
|----------|-------------|
| `PROXY_HTTP_URL` / `PROXY_HTTPS_URL` | Optional HTTP proxies for other tooling (e.g. transcript fetchers) |

## Usage

### Pipeline (summarize JSON → DB → email)

Uses `recent_full_articles.json` in the project root by default.

```bash
uv run python main.py
```

Or:

```bash
uv run python -m app.pipeline
```

Options:

```bash
uv run python -m app.pipeline path/to/articles.json --db data/summaries.db --no-email
```

### Scrape freeCodeCamp (optional)

The scraper writes `recent_full_articles.json`. It expects `requests` and `beautifulsoup4`:

```bash
uv add requests beautifulsoup4
uv run python app/scrapers/freecodecamp.py
```

## Article JSON format

Each item should look like:

```json
{
  "name": "Article title",
  "published_relative": "3 hours ago",
  "timestamp": "2026-03-31T16:00:38.087Z",
  "link": "https://example.com/article",
  "full_content": "Full article text…",
  "source": "FreeCodeCamp"
}
```

## Database

- Default path: `data/summaries.db` (the `data/` folder is ignored by git).
- Table: `article_summaries` — keyed by `link` (upsert on re-runs).

## Project layout

```
├── main.py                 # Entry: runs the pipeline
├── recent_full_articles.json   # Input for the pipeline (from scraper or manual)
├── app/
│   ├── pipeline.py         # Orchestration
│   ├── summarize.py        # LLM backends
│   ├── database.py         # SQLite
│   ├── email_digest.py     # SMTP digest
│   ├── models.py           # Pydantic models
│   ├── config.py           # .env loading
│   └── scrapers/
│       └── freecodecamp.py
├── data/                   # Created at runtime (SQLite)
└── pyproject.toml
```

## License

Add your license here if applicable.
