#!/usr/bin/env python3
"""Boîtes de Leitner pour apprendre les tables de multiplication (1 à 10).

Chaque utilisateur s'inscrit, puis révise des cartes classées dans 5 boîtes :
- bonne réponse : la carte monte d'une boîte (boîte 5 = apprise)
- mauvaise réponse : la carte retombe en boîte 1
Les progrès sont sauvegardés en SQLite, par utilisateur.
"""
import os
import random
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, g, redirect, render_template, request, session, url_for, jsonify,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("LEITNER_DB", os.path.join(BASE_DIR, "leitner.db"))

app = Flask(__name__)
app.secret_key = os.environ.get(
    "LEITNER_SECRET_KEY",
    secrets.token_hex(32),
)

# Une boîte par niveau ; révision d'autant plus espacée que la boîte est haute.
BOXES = 5
INTERVALS = [0, 1, 2, 4, 8]  # en jours : boîte 1 = aujourd'hui, boîte 5 = dans 8 jours

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cards (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            a INTEGER NOT NULL,
            b INTEGER NOT NULL,
            box INTEGER NOT NULL DEFAULT 1,
            due TEXT NOT NULL,
            PRIMARY KEY (user_id, a, b)
        );
        """
    )
    db.commit()
    db.close()


def hash_password(password):
    import hashlib
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password, stored):
    import hashlib
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return secrets.compare_digest(check.hex(), digest)


def all_cards():
    return [(a, b) for a in range(1, 11) for b in range(1, 11)]


def ensure_cards(user_id):
    """Crée les 100 cartes en boîte 1 si l'utilisateur n'en a pas encore."""
    db = get_db()
    if db.execute("SELECT 1 FROM cards WHERE user_id = ?", (user_id,)).fetchone():
        return
    due = datetime.utcnow().isoformat(timespec="seconds")
    db.executemany(
        "INSERT INTO cards (user_id, a, b, box, due) VALUES (?, ?, ?, 1, ?)",
        [(user_id, a, b, due) for a, b in all_cards()],
    )
    db.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        ensure_cards(session["user_id"])
        return view(*args, **kwargs)
    return wrapped


def current_user():
    db = get_db()
    return db.execute(
        "SELECT id, username FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("review"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not USERNAME_RE.match(username):
            error = "Pseudo : 3 à 30 caractères (lettres, chiffres, _ . -)."
        elif len(password) < 4:
            error = "Mot de passe : au moins 4 caractères."
        else:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, hash_password(password), datetime.utcnow().isoformat(timespec="seconds")),
                )
                db.commit()
                session["user_id"] = cur.lastrowid
                return redirect(url_for("review"))
            except sqlite3.IntegrityError:
                error = "Ce pseudo est déjà pris."
    return render_template("auth.html", mode="register", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None or not verify_password(password, user["password_hash"]):
            error = "Pseudo ou mot de passe incorrect."
        else:
            session["user_id"] = user["id"]
            nxt = request.args.get("next")
            if nxt and nxt.startswith("/"):
                return redirect(nxt)
            return redirect(url_for("review"))
    return render_template("auth.html", mode="login", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/revision")
@login_required
def review():
    return render_template("review.html", user=current_user())


@app.route("/api/card")
@login_required
def api_card():
    db = get_db()
    now = datetime.utcnow()
    row = db.execute(
        """SELECT a, b, box FROM cards
           WHERE user_id = ? AND due <= ?
           ORDER BY box ASC, RANDOM() LIMIT 1""",
        (session["user_id"], now.isoformat(timespec="seconds")),
    ).fetchone()
    if row is None:
        return jsonify({"done": True})
    total_due = db.execute(
        "SELECT COUNT(*) AS n FROM cards WHERE user_id = ? AND due <= ?",
        (session["user_id"], now.isoformat(timespec="seconds")),
    ).fetchone()["n"]
    return jsonify({
        "done": False,
        "a": row["a"],
        "b": row["b"],
        "box": row["box"],
        "remaining": total_due,
    })


@app.route("/api/answer", methods=["POST"])
@login_required
def api_answer():
    data = request.get_json(force=True)
    a, b = int(data.get("a")), int(data.get("b"))
    correct = int(data.get("answer")) == a * b
    db = get_db()
    row = db.execute(
        "SELECT box FROM cards WHERE user_id = ? AND a = ? AND b = ?",
        (session["user_id"], a, b),
    ).fetchone()
    if row is None:
        return jsonify({"error": "carte inconnue"}), 404
    if correct:
        new_box = min(BOXES, row["box"] + 1)
    else:
        new_box = 1
    due = (datetime.utcnow() + timedelta(days=INTERVALS[new_box - 1])).isoformat(timespec="seconds")
    db.execute(
        "UPDATE cards SET box = ?, due = ? WHERE user_id = ? AND a = ? AND b = ?",
        (new_box, due, session["user_id"], a, b),
    )
    db.commit()
    return jsonify({"correct": correct, "box": new_box})


@app.route("/api/stats")
@login_required
def api_stats():
    db = get_db()
    now = datetime.utcnow().isoformat(timespec="seconds")
    rows = db.execute(
        "SELECT box, COUNT(*) AS n, SUM(CASE WHEN due <= ? THEN 1 ELSE 0 END) AS due_now "
        "FROM cards WHERE user_id = ? GROUP BY box ORDER BY box",
        (now, session["user_id"]),
    ).fetchall()
    boxes = [{"box": r["box"], "count": r["n"], "due_now": r["due_now"] or 0} for r in rows]
    learned = sum(b["count"] for b in boxes if b["box"] == BOXES)
    due_now = sum(b["due_now"] for b in boxes)
    return jsonify({"boxes": boxes, "learned": learned, "total": len(all_cards()), "due_now": due_now})


@app.route("/profil")
@login_required
def profile():
    return render_template("profile.html", user=current_user())


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
