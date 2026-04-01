"""CLI entrypoint: summarize articles → database → email digest."""

from app.pipelines.digest import main


if __name__ == "__main__":
    main()
