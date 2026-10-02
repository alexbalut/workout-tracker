import { Routes } from '@angular/router';
import { WorkoutPage } from './pages/workout/workout';
import { ProgressPage } from './pages/progress/progress';

export const routes: Routes = [
  { path: '', component: WorkoutPage },
  { path: 'progress', component: ProgressPage },
  { path: '**', redirectTo: '' },
];
