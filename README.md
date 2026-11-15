# CreatorFlow

A video platform backend for AI video creators, built with **FastAPI** and **FFmpeg**.
Users upload a video, the server validates it, stores it safely, and generates
low, medium and high quality versions in the background.

> **Status: work in progress.** The backend core is working. Authentication,
> a job queue, and the React frontend are planned (see the roadmap below).

## Tech stack

- **FastAPI** (Python) for the API
- **SQLAlchemy 2.0** for the ORM
- **Alembic** for database migrations
- **MySQL** for local development (PostgreSQL planned for production)
- **FFmpeg** for video processing (called via `subprocess`)
- **Pydantic** for request and response validation

## What works today

**Uploads**
- Multipart upload with title, optional description, and a video file
- Two-layer file validation: the declared content type is checked first, then the
  file's real bytes are inspected with `filetype`, so a renamed `.txt` is rejected
- Streamed to disk in 1 MB chunks, with a 300 MB size limit
- Files are stored under server-generated UUID names, never the user's filename
  (avoids overwrites, odd characters and path tricks)
- Only verified values (such as the detected MIME type) are saved to the database

**Duplicate detection**
- A SHA-256 hash is computed while the file streams in
- A `UNIQUE` constraint on the hash rejects duplicates with `409 Conflict`
- The check is enforced by the database, so simultaneous uploads cannot slip through

**Video processing**
- FFmpeg generates 640p, 720p-class and 1080p-class versions (low, medium, high)
  without upscaling smaller videos
- Runs as a background task with its own database session
- Status moves through `processing`, then `completed` or `failed`
- A timeout stops hung FFmpeg runs, and partial output is cleaned up on failure
- FFmpeg is invoked with an argument list and no shell, so filenames cannot be
  interpreted as commands

**API**

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/videos/upload` | Upload a video |
| `GET` | `/api/videos/` | List videos |
| `GET` | `/api/videos/{id}` | Get one video |
| `PATCH` | `/api/videos/{id}` | Partially update title or description |
| `DELETE` | `/api/videos/{id}` | Delete a video and all its files |

**Design decisions worth noting**
- `PATCH` uses Pydantic's `exclude_unset` so that "field not sent" and
  "field explicitly set to null" are handled differently
- `DELETE` returns `409` while a video is still processing, rather than racing the
  background task
- File size is returned both as raw bytes and as a readable `file_size_display`
  field, so clients can sort numerically and still show "12.50 MB"
- Database structure is managed only by Alembic migrations, not `create_all`
- Configuration and secrets live in a `.env` file that is never committed

## Getting started

**Prerequisites:** Python 3.10+, MySQL, and [FFmpeg](https://ffmpeg.org/) available on your `PATH`.

```bash
# 1. Clone and enter the backend
git clone <your-repo-url>
cd creator_platform/backend

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the database
#    Copy .env.example to .env and set DATABASE_URL

# 5. Create the database tables
alembic upgrade head

# 6. Run the server
uvicorn app.main:app --reload
```

Interactive API docs are then available at `http://127.0.0.1:8000/docs`.

## Project structure

```
backend/
├── alembic/            # database migrations
├── app/
│   ├── api/            # route handlers
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # FFmpeg video processing
│   ├── database.py     # engine and session setup
│   └── main.py         # FastAPI entry point
├── uploads/            # stored videos (not committed)
├── alembic.ini
└── requirements.txt
```

## Roadmap

- [ ] JWT authentication and per-user ownership checks
- [ ] Job queue and worker (e.g. Redis with ARQ or Celery) for FFmpeg, so processing
      survives server restarts and can be retried
- [ ] Pagination, ordering and filtering for the video list
- [ ] Perceptual hashing to catch re-encoded duplicates (SHA-256 only catches
      byte-identical files)
- [ ] PostgreSQL and deployment
- [ ] React frontend

## Known limitations

- Video processing uses in-process background tasks, so a server restart during
  processing leaves that video stuck in `processing`
- No authentication yet, so every endpoint is open
- Duplicate detection is exact-match only