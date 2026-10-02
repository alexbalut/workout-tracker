import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import {
  ApiService,
  ExerciseInfo,
  SetRow,
  WorkoutSummary,
} from './services/api';
import { todayToronto } from './services/date-util';

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private readonly api = inject(ApiService);

  readonly title = 'Workout Tracker';

  workoutName = '';
  workoutDate = todayToronto();
  activeId: string | null = null;
  activeName = '';
  activeDate = '';

  exercise = '';
  setNumber = 1;
  reps: number | null = null;
  weightLbs: number | null = null;

  exercises = signal<ExerciseInfo[]>([]);
  history = signal<WorkoutSummary[]>([]);
  sets = signal<SetRow[]>([]);
  filteredExercises = signal<ExerciseInfo[]>([]);
  status = signal('');
  error = signal('');
  saving = signal(false);
  showSuggestions = signal(false);

  ngOnInit(): void {
    this.refreshExercises();
    this.refreshHistory();
  }

  refreshExercises(): void {
    this.api.getExercises().subscribe({
      next: (list) => {
        this.exercises.set(list);
        this.updateFiltered();
      },
      error: () => {},
    });
  }

  refreshHistory(): void {
    this.api.getWorkouts().subscribe({
      next: (list) => this.history.set(list),
      error: (err) => this.error.set(err?.error?.detail || 'Failed to load history'),
    });
  }

  updateFiltered(): void {
    const q = this.exercise.trim().toLowerCase();
    const all = this.exercises();
    if (!q) {
      this.filteredExercises.set(all.slice(0, 8));
      return;
    }
    this.filteredExercises.set(
      all.filter((e) => e.name.toLowerCase().includes(q)).slice(0, 8),
    );
  }

  startSession(): void {
    this.error.set('');
    const name = this.workoutName.trim();
    if (!name) {
      this.error.set('Enter a workout name');
      return;
    }
    this.saving.set(true);
    this.api.createWorkout(name, this.workoutDate).subscribe({
      next: (w) => {
        this.activeId = w.id;
        this.activeName = w.workout_name;
        this.activeDate = w.date;
        this.sets.set([]);
        this.setNumber = 1;
        this.status.set(`Session started: ${w.workout_name}`);
        this.saving.set(false);
        this.refreshHistory();
      },
      error: (err) => {
        this.error.set(err?.error?.detail || 'Failed to create workout');
        this.saving.set(false);
      },
    });
  }

  openWorkout(w: WorkoutSummary): void {
    this.error.set('');
    this.api.getWorkout(w.id).subscribe({
      next: (detail) => {
        this.activeId = detail.id;
        this.activeName = detail.workout_name;
        this.activeDate = detail.date;
        this.workoutName = detail.workout_name;
        this.workoutDate = detail.date;
        this.sets.set(detail.sets);
        this.setNumber = this.nextSetNumber(detail.sets, this.exercise);
        this.status.set(`Loaded: ${detail.workout_name}`);
      },
      error: (err) => this.error.set(err?.error?.detail || 'Failed to load workout'),
    });
  }

  onExerciseInput(): void {
    this.updateFiltered();
    this.showSuggestions.set(true);
  }

  pickExercise(e: ExerciseInfo): void {
    this.exercise = e.name;
    this.reps = e.last_reps;
    this.weightLbs = e.last_weight_lbs;
    this.showSuggestions.set(false);
    this.setNumber = this.nextSetNumber(this.sets(), e.name);
    this.updateFiltered();
  }

  onExerciseBlur(): void {
    setTimeout(() => {
      this.showSuggestions.set(false);
      this.applyLastUsedIfKnown();
    }, 150);
  }

  applyLastUsedIfKnown(): void {
    const name = this.exercise.trim().toLowerCase();
    if (!name) return;
    const match = this.exercises().find((e) => e.name.toLowerCase() === name);
    if (match) {
      if (this.reps === null) this.reps = match.last_reps;
      if (this.weightLbs === null) this.weightLbs = match.last_weight_lbs;
    }
    this.setNumber = this.nextSetNumber(this.sets(), this.exercise);
  }

  nextSetNumber(sets: SetRow[], exerciseName: string): number {
    const name = exerciseName.trim().toLowerCase();
    if (!name) return 1;
    const forEx = sets.filter((s) => s.exercise.toLowerCase() === name);
    if (!forEx.length) return 1;
    return Math.max(...forEx.map((s) => s.set_number)) + 1;
  }

  saveSet(): void {
    this.error.set('');
    if (!this.activeId) {
      this.error.set('Start or open a workout session first');
      return;
    }
    const exercise = this.exercise.trim();
    if (!exercise) {
      this.error.set('Enter an exercise name');
      return;
    }
    if (this.reps === null || this.reps < 0) {
      this.error.set('Enter reps (0+)');
      return;
    }
    if (this.weightLbs === null || this.weightLbs < 0) {
      this.error.set('Enter weight in lbs (0 for bodyweight)');
      return;
    }
    this.saving.set(true);
    this.api
      .addSet(this.activeId, {
        exercise,
        set_number: this.setNumber,
        reps: this.reps,
        weight_lbs: this.weightLbs,
      })
      .subscribe({
        next: () => {
          this.status.set(`Saved set ${this.setNumber} — ${exercise}`);
          this.api.getWorkout(this.activeId!).subscribe({
            next: (detail) => {
              this.sets.set(detail.sets);
              this.setNumber = this.nextSetNumber(detail.sets, exercise);
              this.saving.set(false);
              this.refreshExercises();
              this.refreshHistory();
            },
            error: () => this.saving.set(false),
          });
        },
        error: (err) => {
          this.error.set(err?.error?.detail || 'Failed to save set');
          this.saving.set(false);
        },
      });
  }
}
