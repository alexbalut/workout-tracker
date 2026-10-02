"""CSV persistence helpers for workout tracker.

saved_at is stored as ISO-8601 UTC with a trailing Z (e.g. 2026-10-02T09:41:00Z).
"""

from __future__ import annotations

import csv
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

CSV_COLUMNS = [
    "workout_name",
    "date",
    "exercise",
    "set_number",
    "reps",
    "weight_lbs",
    "saved_at",
]

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def ensure_data_dir(data_dir: Path | None = None) -> Path:
    d = data_dir or DATA_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "workout"


def workout_id_from(name: str, workout_date: str) -> str:
    return f"{slugify(name)}_{workout_date}"


def csv_path_for(workout_id: str, data_dir: Path | None = None) -> Path:
    d = ensure_data_dir(data_dir)
    # Prevent path traversal
    safe = Path(workout_id).name
    if safe != workout_id or ".." in workout_id:
        raise ValueError("Invalid workout id")
    return d / f"{safe}.csv"


def utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_workout_csv(
    workout_name: str,
    workout_date: str,
    data_dir: Path | None = None,
) -> dict[str, Any]:
    ensure_data_dir(data_dir)
    wid = workout_id_from(workout_name, workout_date)
    path = csv_path_for(wid, data_dir)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
    return {
        "id": wid,
        "workout_name": workout_name,
        "date": workout_date,
        "filename": path.name,
    }


def append_set(
    workout_id: str,
    exercise: str,
    set_number: int,
    reps: int,
    weight_lbs: float,
    data_dir: Path | None = None,
) -> dict[str, Any]:
    path = csv_path_for(workout_id, data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Workout not found: {workout_id}")

    # Read name/date from existing rows or filename
    workout_name, workout_date = _name_date_from_csv(path, workout_id)
    saved_at = utc_now_iso_z()
    row = {
        "workout_name": workout_name,
        "date": workout_date,
        "exercise": exercise.strip(),
        "set_number": str(set_number),
        "reps": str(reps),
        "weight_lbs": str(weight_lbs),
        "saved_at": saved_at,
    }
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)
    return {
        "workout_id": workout_id,
        "exercise": row["exercise"],
        "set_number": set_number,
        "reps": reps,
        "weight_lbs": weight_lbs,
        "saved_at": saved_at,
    }


def _name_date_from_csv(path: Path, workout_id: str) -> tuple[str, str]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("workout_name") or "").strip()
            d = (row.get("date") or "").strip()
            if name and d:
                return name, d
    # Fallback: parse from id stem slug_YYYY-MM-DD
    m = re.match(r"^(.+)_(\d{4}-\d{2}-\d{2})$", workout_id)
    if m:
        return m.group(1).replace("-", " ").title(), m.group(2)
    return workout_id, date.today().isoformat()


def load_workout(workout_id: str, data_dir: Path | None = None) -> dict[str, Any]:
    path = csv_path_for(workout_id, data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Workout not found: {workout_id}")
    sets: list[dict[str, Any]] = []
    workout_name = ""
    workout_date = ""
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not workout_name:
                workout_name = (row.get("workout_name") or "").strip()
            if not workout_date:
                workout_date = (row.get("date") or "").strip()
            exercise = (row.get("exercise") or "").strip()
            if not exercise:
                continue
            sets.append(
                {
                    "exercise": exercise,
                    "set_number": int(row.get("set_number") or 0),
                    "reps": int(float(row.get("reps") or 0)),
                    "weight_lbs": float(row.get("weight_lbs") or 0),
                    "saved_at": (row.get("saved_at") or "").strip(),
                }
            )
    if not workout_name or not workout_date:
        workout_name, workout_date = _name_date_from_csv(path, workout_id)
    return {
        "id": workout_id,
        "workout_name": workout_name,
        "date": workout_date,
        "filename": path.name,
        "sets": sets,
    }


def list_workouts(limit: int = 20, data_dir: Path | None = None) -> list[dict[str, Any]]:
    d = ensure_data_dir(data_dir)
    files = sorted(d.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    results: list[dict[str, Any]] = []
    for path in files[:limit]:
        wid = path.stem
        try:
            name, wdate = _name_date_from_csv(path, wid)
        except Exception:
            name, wdate = wid, ""
        results.append(
            {
                "id": wid,
                "workout_name": name,
                "date": wdate,
                "filename": path.name,
            }
        )
    return results


def list_exercises(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Unique exercise names across all CSVs with last-used reps/weight."""
    d = ensure_data_dir(data_dir)
    # Map name -> (saved_at, reps, weight) keeping most recent by saved_at then file mtime order
    latest: dict[str, dict[str, Any]] = {}
    files = sorted(d.glob("*.csv"), key=lambda p: p.stat().st_mtime)
    for path in files:
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("exercise") or "").strip()
                if not name:
                    continue
                saved_at = (row.get("saved_at") or "").strip()
                entry = {
                    "name": name,
                    "last_reps": int(float(row.get("reps") or 0)),
                    "last_weight_lbs": float(row.get("weight_lbs") or 0),
                    "saved_at": saved_at,
                }
                prev = latest.get(name.lower())
                if prev is None or (saved_at and saved_at >= (prev.get("saved_at") or "")):
                    latest[name.lower()] = entry
                elif not saved_at:
                    # No timestamp: later file wins (already iterating by mtime)
                    latest[name.lower()] = entry
    return sorted(
        [
            {
                "name": v["name"],
                "last_reps": v["last_reps"],
                "last_weight_lbs": v["last_weight_lbs"],
            }
            for v in latest.values()
        ],
        key=lambda x: x["name"].lower(),
    )
