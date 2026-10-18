# Videoflix Backend

Videoflix is a Django backend for a video streaming application. Its REST API supports user registration, authentication, and authenticated video delivery using HTTP Live Streaming (HLS). Uploaded videos are processed in the background with FFmpeg to generate three resolutions.

This repository contains the backend. A separate frontend is required for the user interface and video playback.

## Features

- Registration using an email address and password
- Email activation with links valid for 24 hours
- JWT authentication using HTTP-only cookies
- Access token renewal and logout with refresh token blacklisting
- Password reset by email with links valid for ten minutes
- Video catalog with titles, descriptions, categories, and thumbnails
- HLS playlists and segments in 480p, 720p, and 1080p
- Background video conversion using Redis and Django RQ
- Video management through Django admin
- Docker Compose configuration for the backend, PostgreSQL, and Redis

## Technology Stack

| Component | Purpose |
| --- | --- |
| Python / Django | Backend and data models |
| Django REST Framework | REST API |
| Simple JWT | Access and refresh tokens |
| PostgreSQL | Users and video metadata |
| Redis / Django RQ | Background jobs; Redis is also configured as a cache |
| FFmpeg | HLS conversion using H.264 video and AAC audio |
| Gunicorn / WhiteNoise | WSGI server and static files |
| Docker Compose | Local services and persistent volumes |

Pinned package versions are listed in `requirements.txt`. The Dockerfile currently uses `python:3.12-alpine`, while Django is pinned to `6.1`. Check compatibility before the first build. Version references in Dockerfile labels and generated comments do not reliably describe the runtime.

### Video Processing

1. An administrator creates a video record with a video file.
2. A `post_save` signal adds three conversion jobs to the `default` queue.
3. The RQ worker uses FFmpeg to generate 480p, 720p, and 1080p versions.
4. Each resolution receives an `index.m3u8` playlist and numbered `.ts` segments, targeting ten seconds per segment.
5. Authenticated users request the playlist and segments through the API.

Conversion starts only when a record is **created with a video file**. Adding or replacing the file later does not trigger another conversion. Processing progress is not exposed through the API. Playlists that are not yet available return HTTP 404. A master playlist for automatic quality selection is not implemented.

## Project Structure

```text
Videoflix/
├── assets/                   # Default thumbnail
├── auth_app/
│   └── api/                  # Registration, login, activation, password reset
├── core/                     # Django settings and root URL configuration
├── video/
│   ├── api/                  # Video catalog, HLS delivery, permissions
│   ├── admin.py              # Video administration
│   ├── models.py             # Video model and upload paths
│   ├── signals.py            # Conversion jobs and file cleanup
│   └── tasks.py              # FFmpeg jobs
├── .env.template             # Local configuration template
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Docker Setup

### Prerequisites

- Git
- Docker with Docker Compose, such as Docker Desktop
- An accessible SMTP service for email delivery
- A compatible frontend with HLS playback for the complete application

### 1. Download the Repository and create env

Clone the repository or download it as a ZIP file. Replace the placeholder with your repository URL:

```bash
git clone https://github.com/Dusty404/Videoflix.git
```

Open a terminal in the downloaded project directory.

Create an project `env`

```powershell
# PowerShell
python -m venv env
```

```bash
# Linux / macOS
python3 -m venv env
```

Activate `env`

```powershell
# PowerShell
env/Scripts/activate
```

```bash
# Linux / macOS
source env/bin/activate
```

Install `requirements`

```powershell
# PowerShell
pip install -r requirements.txt
```

```bash
# Linux / macOS
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.template` to `.env`:

```powershell
# PowerShell
Copy-Item .env.template .env
```

```bash
# Linux / macOS
cp .env.template .env
```

Update `.env` before starting the application. For Docker, keep `DB_HOST=db` and `REDIS_HOST=redis`.

| Variable | Description |
| --- | --- |
| `SECRET_KEY` | Your own Django secret key; replace the example value |
| `DEBUG` | Currently read directly as a string; see Known Limitations |
| `ALLOWED_HOSTS` | Comma-separated backend hostnames without a protocol |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins including the protocol |
| `DJANGO_SUPERUSER_USERNAME` | Administrator username used at startup |
| `DJANGO_SUPERUSER_EMAIL` | Administrator email address |
| `DJANGO_SUPERUSER_PASSWORD` | Administrator password; replace the example value |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL database name and credentials |
| `DB_HOST`, `DB_PORT` | PostgreSQL connection; `db` and `5432` in Docker |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` | RQ connection; defaults: `redis`, `6379`, `0` |
| `REDIS_LOCATION` | Cache connection; default: `redis://redis:6379/1` |
| `EMAIL_HOST`, `EMAIL_PORT` | SMTP server and port |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP credentials |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL` | Present in the template but currently not applied to the email configuration |

For local development, enable the existing commented console backend setting in `core/settings.py`:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

Emails will then appear in the backend logs. The four SMTP variables accessed directly through `os.environ[...]` under `MAILERS` must still exist. The template placeholders can remain for local console output.

### 3. Start the Containers

After checking the Python/Django versions and configuration:

```bash
docker compose up --build -d
docker compose logs -f web
```

The startup script waits for PostgreSQL, collects static files, generates and applies migrations, and creates an administrator if needed. It then starts an RQ worker and Gunicorn in the same container. Changing administrator credentials in `.env` does not update an existing account.

| Address | Purpose |
| --- | --- |
| `http://localhost:8000/admin/` | Django administration |
| `http://localhost:8000/api/` | Base URL for individual API endpoints; no standalone index page |
| `http://localhost:8000/django-rq/` | Queue administration for authorized administrators |

### 4. Add Your First Video

1. Sign in to Django admin using the configured administrator account.
2. Create a new entry under **Videos**.
3. Enter a title, description, category, and video file. Optionally upload a thumbnail.
4. Save and wait for conversion to finish. The configured job timeout is 900 seconds.
5. Access the video through the authenticated catalog and one of its HLS URLs.

Use different source filenames for different videos. Upload directories are derived from filenames. Shared derived directories can cause conflicts during HLS generation and deletion.

## API

Local development base URL: `http://localhost:8000/api/`

JSON requests use `Content-Type: application/json`. Trailing slashes are part of the routes shown below.

### User Accounts

| Method | Path relative to `/api/` | Input / behavior |
| --- | --- | --- |
| POST | `register/` | `email`, `password`, `confirmed_password`; creates an inactive account and sends an activation link |
| GET | `activate/<uidb64>/<token>/` | Activates the account if the link is valid |
| POST | `login/` | `email`, `password`; sets access and refresh cookies |
| POST | `token/refresh/` | Reads the refresh cookie and sets a new access cookie |
| POST | `logout/` | Blacklists the supplied refresh token and removes both cookies |
| POST | `password_reset/` | `email`; sends a reset link if the account exists |
| POST | `password_confirm/<uidb64>/<token>/` | `new_password`, `confirm_password`; resets the password |

### Videos and Streaming

All endpoints below require a valid `access_token` cookie.

| Method | Path relative to `/api/` | Result |
| --- | --- | --- |
| GET | `video/` | Complete video catalog ordered by ID, without pagination |
| GET | `video/<movie_id>/<resolution>/index.m3u8` | HLS playlist |
| GET | `video/<movie_id>/<resolution>/<segment>` | HLS segment, such as `000.ts` |

Allowed `resolution` values: `480p`, `720p`, `1080p`.

Example catalog response; IDs, timestamps, and file paths will vary:

```json
[
  {
    "id": 1,
    "created_at": "2026-01-01T12:00:00Z",
    "title": "Example Video",
    "description": "A description of the video.",
    "thumbnail_url": "http://localhost:8000/media/thumbnails/default.png",
    "category": "Documentary"
  }
]
```

For example, request a playlist at `/api/video/1/720p/index.m3u8`. The player must also send cookies when requesting segments. Public video upload, update, and delete endpoints are not currently available; use Django admin for those operations.

### Cookies and Frontend Integration

The `access_token` and `refresh_token` cookies use `HttpOnly=True`, `Secure=True`, and `SameSite=Lax`.

Video permissions explicitly read the access token from the cookie.

The following frontend origins are hardcoded as allowed CORS origins in `core/settings.py`:

- `http://localhost:4200`
- `http://127.0.0.1:4200`
- `http://localhost:5500`
- `http://127.0.0.1:5500`

Activation and password reset emails use these hardcoded frontend URLs:

```text
http://127.0.0.1:5500/pages/auth/activate.html?uid=...&token=...
http://127.0.0.1:5500/pages/auth/confirm_password.html?uid=...&token=...
```

The frontend must extract these parameters and call the corresponding API endpoint. When using a different frontend address, update the links in `auth_app/api/functions.py` and the allowed origins. Use a consistent hostname for the backend and frontend during local testing.

## Operations and Data Storage

```bash
# Show service status
docker compose ps

# View backend and worker logs
docker compose logs -f web

# Check Django configuration
docker compose exec web python manage.py check

# Run Django tests
docker compose exec web python manage.py test auth_app video

# Stop services
docker compose down
```

Deleting a video record removes its directory under `media/videos/`, including generated HLS files.