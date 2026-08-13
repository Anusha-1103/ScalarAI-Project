# EchoNote API

The FastAPI service persists meetings, participants, transcripts, summaries,
chapters, and action items in SQLite.

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Interactive API documentation is available at `http://localhost:8000/docs`.
