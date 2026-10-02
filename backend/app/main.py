"""Workout Tracker FastAPI backend — CSV file persistence."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import csv_store

TORONTO = ZoneInfo("America/Toronto")

DATA_DIR = Path(os.environ.get("DATA_DIR", str(csv_store.DATA_DIR)))

app = FastAPI(title="Workout Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateWorkout(BaseModel):
    workout_name: str = Field(..., min_length=1, max_length=200)
    date: str | None = None  # YYYY-MM-DD; defaults to today America/Toronto


class AddSet(BaseModel):
    exercise: str = Field(..., min_length=1, max_length=200)
    set_number: int = Field(..., ge=1)
    reps: int = Field(..., ge=0)
    weight_lbs: float = Field(..., ge=0)


def _today_toronto() -> str:
    from datetime import datetime

    return datetime.now(TORONTO).date().isoformat()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/exercises")
def get_exercises():
    return csv_store.list_exercises(DATA_DIR)


@app.get("/api/workouts")
def get_workouts():
    return csv_store.list_workouts(20, DATA_DIR)


@app.post("/api/workouts", status_code=201)
def create_workout(body: CreateWorkout):
    wdate = body.date or _today_toronto()
    try:
        date.fromisoformat(wdate)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    name = body.workout_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="workout_name required")
    return csv_store.create_workout_csv(name, wdate, DATA_DIR)


@app.get("/api/workouts/{workout_id}")
def get_workout(workout_id: str):
    try:
        return csv_store.load_workout(workout_id, DATA_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Workout not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/workouts/{workout_id}/sets", status_code=201)
def add_set(workout_id: str, body: AddSet):
    try:
        return csv_store.append_set(
            workout_id,
            body.exercise,
            body.set_number,
            body.reps,
            body.weight_lbs,
            DATA_DIR,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Workout not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
