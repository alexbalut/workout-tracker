"""Smoke tests for Epley e1RM progress aggregation."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import csv_store


class TestEpleyProgress(unittest.TestCase):
    def test_epley_formula(self):
        # 225 x 5 → 225 * (1 + 5/30) = 225 * 1.166... = 262.5
        self.assertAlmostEqual(csv_store.epley_e1rm(225, 5), 262.5)
        self.assertAlmostEqual(csv_store.epley_e1rm(100, 0), 100.0)
        self.assertAlmostEqual(csv_store.epley_e1rm(135, 10), 180.0)

    def test_progress_aggregation(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            # Day 1: two sets — best is 225x5 (e1rm 262.5) vs 205x8 (e1rm ~259.7)
            p1 = data / "push_2026-09-01.csv"
            with p1.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=csv_store.CSV_COLUMNS)
                w.writeheader()
                w.writerow(
                    {
                        "workout_name": "Push",
                        "date": "2026-09-01",
                        "exercise": "Bench Press",
                        "set_number": "1",
                        "reps": "8",
                        "weight_lbs": "205",
                        "saved_at": "2026-09-01T12:00:00Z",
                    }
                )
                w.writerow(
                    {
                        "workout_name": "Push",
                        "date": "2026-09-01",
                        "exercise": "Bench Press",
                        "set_number": "2",
                        "reps": "5",
                        "weight_lbs": "225",
                        "saved_at": "2026-09-01T12:05:00Z",
                    }
                )
                w.writerow(
                    {
                        "workout_name": "Push",
                        "date": "2026-09-01",
                        "exercise": "Overhead Press",
                        "set_number": "1",
                        "reps": "8",
                        "weight_lbs": "95",
                        "saved_at": "2026-09-01T12:10:00Z",
                    }
                )

            # Day 2: heavier
            p2 = data / "push_2026-09-08.csv"
            with p2.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=csv_store.CSV_COLUMNS)
                w.writeheader()
                w.writerow(
                    {
                        "workout_name": "Push",
                        "date": "2026-09-08",
                        "exercise": "bench press",  # case-insensitive
                        "set_number": "1",
                        "reps": "3",
                        "weight_lbs": "245",
                        "saved_at": "2026-09-08T12:00:00Z",
                    }
                )

            points = csv_store.exercise_progress("Bench Press", data)
            self.assertEqual(len(points), 2)
            self.assertEqual(points[0]["date"], "2026-09-01")
            self.assertEqual(points[1]["date"], "2026-09-08")

            # Day 1: max e1rm from 225x5 = 262.5; volume = 8*205 + 5*225 = 1640+1125 = 2765
            self.assertEqual(points[0]["e1rm"], 262.5)
            self.assertEqual(points[0]["volume"], 2765.0)
            self.assertEqual(points[0]["best_set"], {"reps": 5, "weight_lbs": 225.0})

            # Day 2: 245 * (1 + 3/30) = 245 * 1.1 = 269.5
            self.assertEqual(points[1]["e1rm"], 269.5)
            self.assertEqual(points[1]["volume"], 735.0)
            self.assertEqual(points[1]["best_set"], {"reps": 3, "weight_lbs": 245.0})

    def test_tie_prefers_higher_weight(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            p = data / "test_2026-09-01.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=csv_store.CSV_COLUMNS)
                w.writeheader()
                # Same e1rm: 180*(1+5/30)=210 and 210*(1+0/30)=210
                w.writerow(
                    {
                        "workout_name": "T",
                        "date": "2026-09-01",
                        "exercise": "Squat",
                        "set_number": "1",
                        "reps": "5",
                        "weight_lbs": "180",
                        "saved_at": "2026-09-01T12:00:00Z",
                    }
                )
                w.writerow(
                    {
                        "workout_name": "T",
                        "date": "2026-09-01",
                        "exercise": "Squat",
                        "set_number": "2",
                        "reps": "0",
                        "weight_lbs": "210",
                        "saved_at": "2026-09-01T12:01:00Z",
                    }
                )
            points = csv_store.exercise_progress("squat", data)
            self.assertEqual(len(points), 1)
            self.assertEqual(points[0]["e1rm"], 210.0)
            self.assertEqual(points[0]["best_set"]["weight_lbs"], 210.0)
            self.assertEqual(points[0]["best_set"]["reps"], 0)


if __name__ == "__main__":
    unittest.main()
