# AI News Aggregator

Collect recent developer news articles, summarize them with an LLM, store results in SQLite, and optionally email a digest.

## What it does

1. **Scrape** — Pull recent articles (e.g. from freeCodeCamp) into `data/inbox/recent_full_articles.json`.
2. **Summarize** — Read that JSON, call a configurable LLM per article, produce short digests.
3. **Persist** — Upsert summaries into SQLite (`data/storage/summaries.db` by default).
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

Copy environment variables into `app/.env`, `config/.env`, or a `.env` at the repo root. Files named `.env` are gitignored.

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

**Ollama (local)**

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
| `SMTP_USER` / `SMTP_PASSWORD` | Gmail: use an **App Password** |
| `EMAIL_FROM` | Sender (often same as `SMTP_USER`) |
| `EMAIL_TO` | Comma-separated recipients |
| `SMTP_USE_TLS` | `true` for port 587 (default) |
| `SMTP_USE_SSL` | `true` for port 465 |
| `EMAIL_SUBJECT` | Optional |
| `SKIP_EMAIL` | `true` to skip sending |

## Usage

### Pipeline (summarize → DB → email)

Default input: `data/inbox/recent_full_articles.json`. Copy `data/samples/example_articles.json` there if you need a quick test.

```bash
uv run python main.py
```

Or:

```bash
uv run python -m app.pipelines.digest
```

Options:

```bash
uv run python -m app.pipelines.digest path/to/articles.json --db data/storage/summaries.db --no-email
```

### Scrape freeCodeCamp (optional)

Writes `data/inbox/recent_full_articles.json`.

```bash
uv run python -m app.scrapers.freecodecamp
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

- Default path: `data/storage/summaries.db` (ignored by git).
- Table: `article_summaries` — keyed by `link` (upsert on re-runs).

## Project layout

```
├── main.py                      # CLI entry → digest pipeline
├── config/                      # Optional: config/.env (see .gitignore)
├── data/
│   ├── samples/
│   │   └── example_articles.json   # Tracked example feed
│   ├── inbox/                   # Scraper output + pipeline input (gitignored)
│   └── storage/                 # SQLite DB (gitignored)
├── app/
│   ├── core/                    # config loader, Pydantic models
│   ├── services/              # LLM summarization, SMTP email
│   ├── persistence/           # SQLite
│   ├── pipelines/             # digest workflow
│   └── scrapers/              # freeCodeCamp scraper
└── pyproject.toml
```

## License

Add your license here if applicable.
