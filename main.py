"""Run the summarize → database → email pipeline."""

from pathlib import Path

from app.pipeline import main as pipeline_main


if __name__ == "__main__":
    pipeline_main()
