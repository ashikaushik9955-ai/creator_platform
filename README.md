# CreatorFlow

A video platform backend for AI video creators, built with **FastAPI** and **FFmpeg**.
Users register and log in, upload a video, and the server validates it, stores it
safely, and generates low, medium and high quality versions in the background.
Only the owner of a video can modify or delete it.

> **Status: work in progress.** The backend core and authentication are working.
> A job queue, deployment, and the React frontend are planned (see the roadmap below).

## Tech stack

- **FastAPI** (Python) for the API
- **SQLAlchemy 2.0** for the ORM
- **Alembic** for database migrations
- **MySQL** for local development (PostgreSQL planned for production)
- **FFmpeg** for video processing (called via `subprocess`)
- **Pydantic** for request and response validation
- **JWT** (PyJWT) and **bcrypt** for authentication and password hashing

## What works today

**Authentication and authorization**
- Register with email and password (email normalized to lowercase, password length
  validated against bcrypt's 72-byte limit)
- Passwords are stored only as salted bcrypt hashes and are never returned by the API
- Login returns a short-lived JWT access token (30 minutes)
- Duplicate emails are rejected by a database `UNIQUE` constraint (`409 Conflict`),
  not by a check-then-insert, so simultaneous registrations cannot slip through
- Login returns the same `401` for a wrong email and a wrong password, so responses
  cannot be used to discover which emails are registered
- A reusable `get_current_user` dependency validates the token on protected routes
- Every video has an owner (foreign key to the user); only the owner can update or delete it
- Ownership failures return `404`, not `403`, so the API does not confirm that
  someone else's video exists

**Uploads**
- Multipart upload with title, optional description, and a video file (login required)
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
- FFmpeg generates low (640 px), medium (1280 px) and high (1920 px) wide versions
  without upscaling smaller videos
- Runs as a background task with its own database session
- Status moves through `processing`, then `completed` or `failed`
- A timeout stops hung FFmpeg runs, and partial output is cleaned up on failure
- FFmpeg is invoked with an argument list and no shell, so filenames cannot be
  interpreted as commands

**API**

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Create an account |
| `POST` | `/api/auth/login` | No | Get an access token |
| `GET` | `/api/auth/me` | Yes | Get the current user |
| `POST` | `/api/videos/upload` | Yes | Upload a video |
| `GET` | `/api/videos/` | No | List videos |
| `GET` | `/api/videos/{id}` | No | Get one video |
| `PATCH` | `/api/videos/{id}` | Yes (owner) | Partially update title or description |
| `DELETE` | `/api/videos/{id}` | Yes (owner) | Delete a video and all its files |

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

# 4. Configure the environment
#    Copy .env.example to .env, then set DATABASE_URL and SECRET_KEY.
#    Generate a SECRET_KEY with:
#    python -c "import secrets; print(secrets.token_hex(32))"

# 5. Create the database tables
alembic upgrade head

# 6. Run the server
uvicorn app.main:app --reload
```

Interactive API docs are then available at `http://127.0.0.1:8000/docs`.
To try protected routes there, register a user, click **Authorize**, and log in with
your email as the username.

## Project structure

```
backend/
├── alembic/            # database migrations
├── app/
│   ├── api/            # route handlers (auth, videos)
│   ├── models/         # SQLAlchemy models (User, Video)
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # FFmpeg video processing
│   ├── database.py     # engine and session setup
│   ├── dependencies.py # get_current_user
│   ├── security.py     # password hashing and JWT creation
│   └── main.py         # FastAPI entry point
├── uploads/            # stored videos (not committed)
├── alembic.ini
└── requirements.txt
```

## Roadmap

- [ ] Pagination, ordering and filtering for the video list
- [ ] CORS configuration for the frontend
- [ ] PostgreSQL and deployment (Docker image that includes FFmpeg)
- [ ] Job queue and worker (e.g. Redis with ARQ or Celery) for FFmpeg, so processing
      survives server restarts and can be retried
- [ ] Perceptual hashing to catch re-encoded duplicates (SHA-256 only catches
      byte-identical files)
- [ ] React frontend

## Known limitations

- Video processing uses in-process background tasks, so a server restart during
  processing leaves that video stuck in `processing`
- Access tokens expire after 30 minutes and there is no refresh-token flow yet
- Duplicate detection is exact-match only and applies across the whole platform
- Listing and viewing videos is public; there are no private videos yet