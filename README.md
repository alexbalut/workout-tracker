# Workout Tracker

Simple private workout logger: name a session, add exercises with reps/weight, each set appends immediately to a CSV. Autocomplete uses exercise names across all past CSVs and prefills last-used reps/weight.

**Stack:** Angular 22 frontend · FastAPI + uvicorn · CSV files (no database) · Docker Compose (nginx + API on port **8080**)

## Quick start (production / Tiny)

```bash
git clone https://github.com/alexbalut/workout-tracker.git
cd workout-tracker
docker compose up --build
```

Open **http://localhost:8080**

Stop with `Ctrl+C`, or run detached:

```bash
docker compose up --build -d
docker compose down
```

Workout CSVs live in `./data` on the host (Docker volume bind). One file per session:

`slug(workout-name)_YYYY-MM-DD.csv`

### CSV columns

```
workout_name,date,exercise,set_number,reps,weight_lbs,saved_at
```

`saved_at` is **ISO-8601 UTC with trailing `Z`** (e.g. `2026-10-02T14:30:00Z`) for consistent sorting across machines. Session **date** defaults to today in **America/Toronto**.

## Features (V1)

1. Name a workout + date (default today America/Toronto)
2. Exercise autocomplete from unique names across all CSVs
3. Sets: reps + weight_lbs (0 allowed for bodyweight)
4. Saving a set appends a CSV row immediately
5. Soft default: known exercise prefills last-used reps/weight
6. History: last 20 workouts
7. No auth

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/exercises` | Unique names + last used reps/weight |
| GET | `/api/workouts` | Last 20 workouts |
| POST | `/api/workouts` | Create session `{ workout_name, date? }` |
| GET | `/api/workouts/{id}` | Load sets from that CSV |
| POST | `/api/workouts/{id}/sets` | Append set `{ exercise, set_number, reps, weight_lbs }` |

## Local development (optional)

### API only

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DATA_DIR=../data uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend (Angular)

```bash
cd frontend
npm install
npm start
```

Dev server: http://localhost:4200 (proxies `/api` → `http://127.0.0.1:8000`)

### Build frontend only

```bash
cd frontend
npm ci
npm run build
```

## Layout

```
workout-tracker/
  README.md
  docker-compose.yml
  .dockerignore
  .gitignore
  data/.gitkeep
  backend/
    Dockerfile
    requirements.txt
    app/main.py
    app/csv_store.py
  frontend/
    Dockerfile
    nginx.conf
    proxy.conf.json
    (Angular 22 app)
```

## License

Private — all rights reserved.
