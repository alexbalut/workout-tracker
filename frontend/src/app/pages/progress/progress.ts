import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import {
  ApiService,
  ExerciseInfo,
  ProgressPoint,
} from '../../services/api';

@Component({
  selector: 'app-progress',
  imports: [CommonModule, FormsModule, BaseChartDirective],
  templateUrl: './progress.html',
  styleUrl: './progress.scss',
})
export class ProgressPage implements OnInit {
  private readonly api = inject(ApiService);

  exercise = '';
  exercises = signal<ExerciseInfo[]>([]);
  filteredExercises = signal<ExerciseInfo[]>([]);
  showSuggestions = signal(false);
  showVolume = signal(true);
  points = signal<ProgressPoint[]>([]);
  selectedName = signal('');
  loading = signal(false);
  error = signal('');
  status = signal('');

  chartData: ChartData<'line'> = { labels: [], datasets: [] };

  chartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { position: 'top' },
      tooltip: {
        callbacks: {
          afterBody: (items) => {
            const idx = items[0]?.dataIndex;
            if (idx === undefined) return '';
            const p = this.points()[idx];
            if (!p) return '';
            return `Best set: ${p.best_set.weight_lbs} lb × ${p.best_set.reps}`;
          },
        },
      },
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: 'Est. 1RM (lbs)' },
        beginAtZero: false,
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: { display: true, text: 'Volume (lbs)' },
        grid: { drawOnChartArea: false },
        beginAtZero: true,
      },
      x: {
        title: { display: true, text: 'Date' },
      },
    },
  };

  ngOnInit(): void {
    this.api.getExercises().subscribe({
      next: (list) => {
        this.exercises.set(list);
        this.updateFiltered();
      },
      error: () => {},
    });
  }

  updateFiltered(): void {
    const q = this.exercise.trim().toLowerCase();
    const all = this.exercises();
    if (!q) {
      this.filteredExercises.set(all.slice(0, 10));
      return;
    }
    this.filteredExercises.set(
      all.filter((e) => e.name.toLowerCase().includes(q)).slice(0, 10),
    );
  }

  onExerciseInput(): void {
    this.updateFiltered();
    this.showSuggestions.set(true);
  }

  pickExercise(e: ExerciseInfo): void {
    this.exercise = e.name;
    this.showSuggestions.set(false);
    this.loadProgress(e.name);
  }

  onExerciseBlur(): void {
    setTimeout(() => this.showSuggestions.set(false), 150);
  }

  loadSelected(): void {
    const name = this.exercise.trim();
    if (!name) {
      this.error.set('Pick an exercise');
      return;
    }
    this.loadProgress(name);
  }

  toggleVolume(): void {
    this.showVolume.update((v) => !v);
    this.rebuildChart(this.points());
  }

  private loadProgress(name: string): void {
    this.error.set('');
    this.status.set('');
    this.loading.set(true);
    this.selectedName.set(name);
    this.api.getExerciseProgress(name).subscribe({
      next: (pts) => {
        this.points.set(pts);
        this.rebuildChart(pts);
        this.loading.set(false);
        if (!pts.length) {
          this.status.set(`No logged sets for “${name}” yet.`);
        } else {
          this.status.set(`${pts.length} session${pts.length === 1 ? '' : 's'} for ${name}`);
        }
      },
      error: (err) => {
        this.error.set(err?.error?.detail || 'Failed to load progress');
        this.loading.set(false);
        this.points.set([]);
        this.rebuildChart([]);
      },
    });
  }

  private rebuildChart(pts: ProgressPoint[]): void {
    const labels = pts.map((p) => p.date);
    const e1rmData = pts.map((p) => p.e1rm);
    const volumeData = pts.map((p) => p.volume);
    const showVol = this.showVolume();

    const datasets: ChartData<'line'>['datasets'] = [
      {
        label: 'Est. 1RM (lbs)',
        data: e1rmData,
        borderColor: '#1570ef',
        backgroundColor: 'rgba(21, 112, 239, 0.15)',
        tension: 0.25,
        pointRadius: 4,
        yAxisID: 'y',
      },
    ];

    if (showVol) {
      datasets.push({
        label: 'Volume (lbs)',
        data: volumeData,
        borderColor: '#12b76a',
        backgroundColor: 'rgba(18, 183, 106, 0.12)',
        tension: 0.25,
        pointRadius: 3,
        borderDash: [6, 4],
        yAxisID: 'y1',
      });
    }

    this.chartOptions = {
      ...this.chartOptions,
      scales: {
        ...this.chartOptions?.scales,
        y1: {
          type: 'linear',
          display: showVol,
          position: 'right',
          title: { display: showVol, text: 'Volume (lbs)' },
          grid: { drawOnChartArea: false },
          beginAtZero: true,
        },
      },
    };

    this.chartData = { labels, datasets };
  }
}
