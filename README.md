# GrindMate

Friend-group DSA tracker — daily LeetCode sync, streaks, group leaderboards, weekly challenges.

> Tu aur tere doston ka private LeetCode tracker. Sab apna LeetCode handle daalo, app automatically scrape karega aur compare karega.

---

## Stack

| Layer | Tooling |
|--------------|--------------------------------------------------------------------------------------------------|
| Backend | Django 5 · Django REST Framework · simplejwt · django-celery-beat · django-celery-results · whitenoise |
| Database | PostgreSQL (prod) · SQLite (dev fallback) |
| Cache/Queue | Redis (prod) · LocMem (dev fallback) · Celery + Beat |
| Frontend | Vite · React 19 · TypeScript · Tailwind CSS · TanStack Query · Zustand · React Router · Axios · React Hook Form · Zod |
| Quality | pytest-django · factory_boy · responses · freezegun · ruff · ESLint · GitHub Actions |
| Deploy | Railway / Render (API) · Vercel (web) |

60 backend tests · ~83% coverage · frontend typecheck + lint clean.

---

## Repo layout

```
Grindmate/
├── backend/ Django + DRF
│ ├── grindmate/ project (settings split, celery, urls)
│ │ └── settings/ base · development · production · test
│ ├── apps/
│ │ ├── users/ custom User, JWT auth, email verification
│ │ ├── leetcode/ GraphQL client, sync, SubmissionLog, periodic task
│ │ └── groups/ Group + Membership + Invite + leaderboard
│ ├── requirements/ base · dev · prod
│ └── manage.py
├── frontend/ Vite + React + TypeScript
│ └── src/
│ ├── components/ ui/ (Button, Card, ...) + layout/
│ ├── pages/ Login · Signup · Dashboard · Account · Groups · GroupDetail · Join
│ ├── lib/ api (axios + JWT refresh) · queryClient · utils
│ ├── stores/ auth (Zustand, persisted)
│ └── types/ api (DRF response types)
├── docker-compose.yml Postgres + Redis for local dev
├── .github/workflows/ci.yml
└── README.md
```

---

## Quick start (local dev)

### Prerequisites
- Python **3.12+**
- Node **20+**
- Docker is **optional** — without it the backend uses SQLite + LocMem cache and runs Celery in-process.

### 1. Clone & env files

```bash
git clone <repo>
cd Grindmate
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. (Optional) Spin up Postgres + Redis

```bash
docker compose up -d # Postgres :5432, Redis :6379
```

If you skip this step, leave `DATABASE_URL` blank in `backend/.env` — Django falls back to SQLite, and dev settings switch the cache to in-memory automatically. Set `DJANGO_DEV_USE_REDIS=1` to opt back into Redis.

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend on `http://localhost:8000`. Admin at `/admin/`. API at `/api/v1/`. Health probe at `/health/`.

For real Celery (only needed when testing periodic sync against the live LeetCode API):

```bash
celery -A grindmate worker -l info
celery -A grindmate beat -l info # schedules pre-registered via data migration
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend on `http://localhost:5173`. The Vite dev server proxies `/api` → `localhost:8000`, so no CORS dance during dev.

---

## Common commands

```bash
# Backend
python manage.py sync_leetcode --user=anveet # manual sync for one user
python manage.py sync_leetcode --all # sync every linked account
pytest # 60 tests
pytest --cov # with coverage report
ruff check . # lint
ruff format . # auto-format

# Frontend
npm run dev # Vite dev server (with API proxy)
npm run build # production bundle
npm run lint # ESLint
npm run typecheck # tsc -b --noEmit
```

---

## Architecture notes

- **JWT auth** with rotated refresh tokens (`djangorestframework-simplejwt`). Frontend stores them in a persisted Zustand store; an axios interceptor refreshes once on 401 and retries.
- **LeetCode sync** uses the unofficial `leetcode.com/graphql` endpoint with retries on rate limit. Sync failures are surfaced — never silently swallowed. Manual mark-solved is a first-class fallback.
- **Leaderboard** is a single annotated query (`Coalesce(Count, 0)` per difficulty + a `Sum(Case(...))` for the difficulty-weighted score), then streaks computed in Python from one prefetched date list. Cached for 60s in Redis (or LocMem in dev), invalidated by a `post_save` signal on `SubmissionLog`.
- **Custom managers**: `SubmissionLog.objects.this_week()`, `.today()`, `.by_difficulty()`, `.distinct_solved_dates(user)`.
- **Data migration**: `apps/leetcode/migrations/0002_register_sync_schedule.py` registers the periodic task with django-celery-beat at deploy time — no manual admin clicks.
- **API versioning**: everything under `/api/v1/`.

---

## Deployment outline

1. **Backend (Railway / Render):**
 - Postgres + Redis addons
 - Env: `DJANGO_SETTINGS_MODULE=grindmate.settings.production`, `DJANGO_SECRET_KEY=<random>`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`, `CORS_ALLOWED_ORIGINS=<vercel url>`, `SENTRY_DSN` (optional)
 - Start commands:
 - Web: `gunicorn grindmate.wsgi --bind 0.0.0.0:$PORT`
 - Worker: `celery -A grindmate worker -l info`
 - Beat: `celery -A grindmate beat -l info`
 - Release: `python manage.py migrate --noinput && python manage.py collectstatic --noinput`
2. **Frontend (Vercel):**
 - Root: `frontend/`
 - Build command: `npm run build` · Output: `dist/`
 - Env: `VITE_API_BASE_URL=https://<api-domain>/api/v1`

---

## License

MIT.
