# Gym Workout Tracker

Built by Manaswin Tripathi (@manaswintripathi)

A simple, fast workout tracker for the gym. Log your lifts, get progressive-overload targets, watch your strength climb on per-exercise charts, and keep your training streak alive.

## Features

- **Log workouts** — date, exercise, sets, reps, weight and notes, with a preloaded exercise list (bench press, squat, deadlift, overhead press, rows, pull-ups and more)
- **Progressive overload hints** — shows your last best set for each exercise and suggests the next target weight/reps (+2.5 kg once you hit 8 reps)
- **Progress charts** — per-exercise weight-over-time line chart drawn on a plain canvas (no external CDN, works offline), plus a weekly volume summary
- **Personal records page** — heaviest set per exercise, with the date it was hit
- **Add / edit / delete entries** — filter history by exercise and date range
- **Streak counter** — consecutive training days, ending today or yesterday
- **Sample data included** — two weeks of realistic workouts are seeded on first run, and can be cleared in one click from the History section

## Tech stack

- Python 3 + Flask (only dependency)
- SQLite via the Python standard library (`sqlite3`) — no ORM, no extra database setup
- Vanilla HTML / CSS / JavaScript frontend — no build step, no CDN dependency

## Setup & run

```bash
git clone https://github.com/manaswintripathi/gym-workout-tracker.git
cd gym-workout-tracker
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

The SQLite database (`workouts.db`) is created automatically on first run and seeded with sample workouts. It is git-ignored, so your own data never gets committed.

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/exercises` | Preloaded + previously used exercises |
| GET / POST | `/api/workouts` | List (filter with `?exercise=&from=&to=`) / add a workout |
| PUT / DELETE | `/api/workouts/<id>` | Edit / delete one entry |
| POST | `/api/workouts/clear` | Delete all entries (clears sample data) |
| GET | `/api/overload/<exercise>` | Last best set + next target |
| GET | `/api/stats/<exercise>` | Per-date max weight, volume, weekly volume |
| GET | `/api/prs` | Personal record per exercise |
| GET | `/api/summary` | Totals, training days, streak, weekly volume |

## How progressive overload works

- Hit **8+ reps** on your last set and the app suggests **+2.5 kg** next session.
- Below 8 reps, it tells you to build up to 8 reps at the same weight first.
- Bodyweight moves (e.g. pull-ups) suggest adding a rep per set.

## License

MIT — free to use and modify.

---
Built by Manaswin Tripathi (@manaswintripathi)
