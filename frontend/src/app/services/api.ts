import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ExerciseInfo {
  name: string;
  last_reps: number;
  last_weight_lbs: number;
}

export interface WorkoutSummary {
  id: string;
  workout_name: string;
  date: string;
  filename: string;
}

export interface SetRow {
  exercise: string;
  set_number: number;
  reps: number;
  weight_lbs: number;
  saved_at: string;
}

export interface WorkoutDetail extends WorkoutSummary {
  sets: SetRow[];
}

export interface ProgressPoint {
  date: string;
  e1rm: number;
  volume: number;
  best_set: { reps: number; weight_lbs: number };
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api';

  getExercises(): Observable<ExerciseInfo[]> {
    return this.http.get<ExerciseInfo[]>(`${this.base}/exercises`);
  }

  getExerciseProgress(name: string): Observable<ProgressPoint[]> {
    return this.http.get<ProgressPoint[]>(
      `${this.base}/exercises/${encodeURIComponent(name)}/progress`,
    );
  }

  getWorkouts(): Observable<WorkoutSummary[]> {
    return this.http.get<WorkoutSummary[]>(`${this.base}/workouts`);
  }

  createWorkout(workout_name: string, date: string): Observable<WorkoutSummary> {
    return this.http.post<WorkoutSummary>(`${this.base}/workouts`, {
      workout_name,
      date,
    });
  }

  getWorkout(id: string): Observable<WorkoutDetail> {
    return this.http.get<WorkoutDetail>(`${this.base}/workouts/${encodeURIComponent(id)}`);
  }

  addSet(
    id: string,
    body: { exercise: string; set_number: number; reps: number; weight_lbs: number },
  ): Observable<unknown> {
    return this.http.post(`${this.base}/workouts/${encodeURIComponent(id)}/sets`, body);
  }
}
