# Built by Manaswin Tripathi (@manaswintripathi)
"""
Gym Workout Tracker — log workouts, track progressive overload,
view personal records and per-exercise progress charts.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""
import os
import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, g, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "workouts.db")

app = Flask(__name__)

EXERCISES = [
    "Bench Press", "Squat", "Deadlift", "Overhead Press", "Barbell Row",
    "Pull-Up", "Lat Pulldown", "Dumbbell Curl", "Triceps Pushdown",
    "Leg Press", "Leg Curl", "Calf Raise", "Incline Bench Press",
    "Dumbbell Shoulder Press", "Seated Cable Row", "Plank",
]

# ---------------------------------------------------------------- DB helpers
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            exercise TEXT NOT NULL,
            sets INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            weight REAL NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )"""
    )
    db.commit()
    count = db.execute("SELECT COUNT(*) FROM workouts").fetchone()[0]
    if count == 0:
        seed(db)
    db.close()


def seed(db):
    """Two weeks of realistic sample workouts. Clearable from the UI."""
    today = date.today()
    samples = [
        # (days_ago, exercise, sets, reps, weight, notes)
        (13, "Bench Press", 4, 8, 60, "Sample data — clear from the UI"),
        (13, "Incline Bench Press", 3, 10, 45, "Sample data — clear from the UI"),
        (13, "Triceps Pushdown", 3, 12, 27.5, "Sample data — clear from the UI"),
        (12, "Squat", 4, 8, 80, "Sample data — clear from the UI"),
        (12, "Leg Press", 3, 12, 120, "Sample data — clear from the UI"),
        (12, "Calf Raise", 3, 15, 50, "Sample data — clear from the UI"),
        (11, "Deadlift", 4, 6, 100, "Sample data — clear from the UI"),
        (11, "Barbell Row", 4, 8, 55, "Sample data — clear from the UI"),
        (11, "Lat Pulldown", 3, 10, 55, "Sample data — clear from the UI"),
        (10, "Overhead Press", 4, 8, 40, "Sample data — clear from the UI"),
        (10, "Dumbbell Shoulder Press", 3, 10, 20, "Sample data — clear from the UI"),
        (10, "Dumbbell Curl", 3, 12, 14, "Sample data — clear from the UI"),
        (8, "Bench Press", 4, 8, 62.5, "Sample data — clear from the UI"),
        (8, "Incline Bench Press", 3, 10, 47.5, "Sample data — clear from the UI"),
        (8, "Triceps Pushdown", 3, 12, 30, "Sample data — clear from the UI"),
        (7, "Squat", 4, 8, 85, "Sample data — clear from the UI"),
        (7, "Leg Press", 3, 12, 130, "Sample data — clear from the UI"),
        (7, "Leg Curl", 3, 12, 45, "Sample data — clear from the UI"),
        (6, "Deadlift", 4, 5, 105, "Sample data — clear from the UI"),
        (6, "Barbell Row", 4, 8, 57.5, "Sample data — clear from the UI"),
        (6, "Pull-Up", 3, 8, 0, "Bodyweight"),
        (5, "Overhead Press", 4, 8, 42.5, "Sample data — clear from the UI"),
        (5, "Dumbbell Curl", 3, 12, 16, "Sample data — clear from the UI"),
        (3, "Bench Press", 4, 7, 65, "Sample data — clear from the UI"),
        (3, "Incline Bench Press", 3, 10, 50, "Sample data — clear from the UI"),
        (2, "Squat", 4, 7, 87.5, "Sample data — clear from the UI"),
        (2, "Leg Press", 3, 12, 140, "Sample data — clear from the UI"),
        (1, "Deadlift", 4, 5, 110, "Sample data — clear from the UI"),
        (1, "Barbell Row", 4, 8, 60, "Sample data — clear from the UI"),
        (0, "Overhead Press", 4, 7, 45, "Sample data — clear from the UI"),
        (0, "Dumbbell Shoulder Press", 3, 10, 22, "Sample data — clear from the UI"),
    ]
    now = datetime.now().isoformat(timespec="seconds")
    for days_ago, ex, sets, reps, weight, notes in samples:
        d = (today - timedelta(days=days_ago)).isoformat()
        db.execute(
            "INSERT INTO workouts (date, exercise, sets, reps, weight, notes, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (d, ex, sets, reps, weight, notes, now),
        )
    db.commit()


def row_to_dict(row):
    d = dict(row)
    d["volume"] = round(d["sets"] * d["reps"] * d["weight"], 1)
    return d


def compute_streak(db):
    """Consecutive days (ending today or yesterday) with at least one workout."""
    dates = {r[0] for r in db.execute("SELECT DISTINCT date FROM workouts")}
    if not dates:
        return 0
    streak = 0
    cursor = date.today()
    if cursor.isoformat() not in dates:
        cursor -= timedelta(days=1)
    while cursor.isoformat() in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


# ------------------------------------------------------------------ pages
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------------------------------------------------- APIs
@app.route("/api/exercises")
def api_exercises():
    db = get_db()
    used = [r[0] for r in db.execute(
        "SELECT DISTINCT exercise FROM workouts ORDER BY exercise")]
    merged = EXERCISES + [e for e in used if e not in EXERCISES]
    return jsonify({"exercises": merged})


@app.route("/api/workouts", methods=["GET", "POST"])
def api_workouts():
    db = get_db()
    if request.method == "POST":
        data = request.get_json(force=True)
        exercise = (data.get("exercise") or "").strip()
        try:
            sets = int(data.get("sets", 0))
            reps = int(data.get("reps", 0))
            weight = float(data.get("weight", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "sets, reps and weight must be numbers"}), 400
        if not exercise or sets <= 0 or reps <= 0 or weight < 0:
            return jsonify({"error": "exercise, sets > 0, reps > 0, weight >= 0 required"}), 400
        wdate = (data.get("date") or date.today().isoformat()).strip()
        notes = (data.get("notes") or "").strip()
        cur = db.execute(
            "INSERT INTO workouts (date, exercise, sets, reps, weight, notes, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (wdate, exercise, sets, reps, weight, notes,
             datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        row = db.execute("SELECT * FROM workouts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(row_to_dict(row)), 201

    exercise = request.args.get("exercise", "").strip()
    date_from = request.args.get("from", "").strip()
    date_to = request.args.get("to", "").strip()
    query = "SELECT * FROM workouts WHERE 1=1"
    params = []
    if exercise:
        query += " AND exercise = ?"
        params.append(exercise)
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    query += " ORDER BY date DESC, id DESC"
    rows = db.execute(query, params).fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/workouts/<int:wid>", methods=["PUT", "DELETE"])
def api_workout(wid):
    db = get_db()
    row = db.execute("SELECT * FROM workouts WHERE id = ?", (wid,)).fetchone()
    if row is None:
        return jsonify({"error": "workout not found"}), 404
    if request.method == "DELETE":
        db.execute("DELETE FROM workouts WHERE id = ?", (wid,))
        db.commit()
        return jsonify({"deleted": wid})
    data = request.get_json(force=True)
    fields = {}
    for key in ("date", "exercise", "notes"):
        if key in data and str(data[key]).strip():
            fields[key] = str(data[key]).strip()
    for key in ("sets", "reps"):
        if key in data:
            try:
                fields[key] = int(data[key])
            except (TypeError, ValueError):
                return jsonify({"error": f"{key} must be an integer"}), 400
    if "weight" in data:
        try:
            fields["weight"] = float(data["weight"])
        except (TypeError, ValueError):
            return jsonify({"error": "weight must be a number"}), 400
    if not fields:
        return jsonify({"error": "nothing to update"}), 400
    assignments = ", ".join(f"{k} = ?" for k in fields)
    db.execute(f"UPDATE workouts SET {assignments} WHERE id = ?",
               list(fields.values()) + [wid])
    db.commit()
    updated = db.execute("SELECT * FROM workouts WHERE id = ?", (wid,)).fetchone()
    return jsonify(row_to_dict(updated))


@app.route("/api/workouts/clear", methods=["POST"])
def api_clear():
    db = get_db()
    db.execute("DELETE FROM workouts")
    db.commit()
    return jsonify({"cleared": True})


@app.route("/api/overload/<path:exercise>")
def api_overload(exercise):
    """Last best set for an exercise + a progressive-overload suggestion."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM workouts WHERE exercise = ? ORDER BY date DESC, id DESC",
        (exercise,),
    ).fetchall()
    if not rows:
        return jsonify({"exercise": exercise, "last_best": None,
                        "suggestion": "No history yet — log your first set to get a target."})
    best = max(rows, key=lambda r: (r["weight"], r["reps"]))
    last = rows[0]
    if last["reps"] >= 8 and last["weight"] > 0:
        target_weight = round(last["weight"] + 2.5, 1)
        suggestion = (f"Last session: {last['sets']}x{last['reps']} @ {last['weight']} kg. "
                      f"Try {last['sets']}x{last['reps']} @ {target_weight} kg (+2.5 kg).")
    elif last["reps"] >= 8:
        suggestion = (f"Last session: {last['sets']}x{last['reps']} bodyweight. "
                      "Try one more rep per set, or add weight.")
    else:
        suggestion = (f"Last session: {last['sets']}x{last['reps']} @ {last['weight']} kg. "
                      f"Build to {last['sets']}x8 @ {last['weight']} kg before adding weight.")
    return jsonify({
        "exercise": exercise,
        "last_best": row_to_dict(best),
        "last_session": row_to_dict(last),
        "suggestion": suggestion,
    })


@app.route("/api/stats/<path:exercise>")
def api_stats(exercise):
    """Per-date max weight + volume for the chart, plus weekly volume."""
    db = get_db()
    rows = db.execute(
        "SELECT date, MAX(weight) AS max_weight, "
        "SUM(sets * reps * weight) AS volume, SUM(sets * reps) AS total_reps "
        "FROM workouts WHERE exercise = ? GROUP BY date ORDER BY date",
        (exercise,),
    ).fetchall()
    points = [{"date": r["date"], "max_weight": r["max_weight"],
               "volume": round(r["volume"] or 0, 1),
               "total_reps": r["total_reps"]} for r in rows]
    week_ago = (date.today() - timedelta(days=6)).isoformat()
    weekly = db.execute(
        "SELECT SUM(sets * reps * weight) FROM workouts WHERE date >= ?",
        (week_ago,),
    ).fetchone()[0] or 0
    return jsonify({"exercise": exercise, "points": points,
                    "weekly_volume_kg": round(weekly, 1)})


@app.route("/api/prs")
def api_prs():
    """Personal record (heaviest single set) per exercise."""
    db = get_db()
    rows = db.execute(
        "SELECT exercise, MAX(weight) AS pr_weight FROM workouts "
        "GROUP BY exercise ORDER BY pr_weight DESC"
    ).fetchall()
    result = []
    for r in rows:
        best = db.execute(
            "SELECT * FROM workouts WHERE exercise = ? ORDER BY weight DESC, date DESC LIMIT 1",
            (r["exercise"],),
        ).fetchone()
        result.append({"exercise": r["exercise"],
                       "pr_weight": r["pr_weight"],
                       "entry": row_to_dict(best)})
    return jsonify(result)


@app.route("/api/summary")
def api_summary():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM workouts").fetchone()[0]
    week_ago = (date.today() - timedelta(days=6)).isoformat()
    weekly = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(sets * reps * weight), 0) FROM workouts WHERE date >= ?",
        (week_ago,),
    ).fetchone()
    days = db.execute("SELECT COUNT(DISTINCT date) FROM workouts").fetchone()[0]
    return jsonify({
        "total_workouts": total,
        "training_days": days,
        "streak_days": compute_streak(db),
        "this_week_workouts": weekly[0],
        "this_week_volume_kg": round(weekly[1], 1),
    })


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
