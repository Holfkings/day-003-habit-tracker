"""Tests para el Habit Tracker CLI.

Usan los subcomandos reales del parser:
  category add|list|delete
  habit add|list|show|update|stats|streaks|logs
  log today|add
  search <query>
  today
  streak
  delete habit|category
  category-habits <id>
"""
import os
import shutil
import subprocess
import sys

DB_PATH = os.path.expanduser("~/.habit_tracker/habits.db")
DB_BACKUP = None


def _restore_db() -> None:
    global DB_BACKUP
    if DB_BACKUP is not None:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        shutil.move(DB_BACKUP, DB_PATH)
        DB_BACKUP = None
    elif os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def _backup_db() -> None:
    global DB_BACKUP
    _restore_db()
    if os.path.exists(DB_PATH):
        DB_BACKUP = DB_PATH + ".bak"
        shutil.copy2(DB_PATH, DB_BACKUP)
    else:
        DB_BACKUP = None


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return subprocess.run(
        [sys.executable, os.path.join(repo_root, "habit.py"), *args],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------

class TestCategory:
    def setup_method(self) -> None:
        _backup_db()

    def teardown_method(self) -> None:
        _restore_db()

    def test_create_and_list(self) -> None:
        r = _run("category", "add", "Salud", "-d", "Hábitos saludables")
        assert r.returncode == 0, r.stderr
        assert "Salud" in r.stdout or "ID:" in r.stdout
        r2 = _run("category", "list")
        assert r2.returncode == 0
        assert "Salud" in r2.stdout


# ---------------------------------------------------------------------------
# Hábitos
# ---------------------------------------------------------------------------

class TestHabit:
    def setup_method(self) -> None:
        _backup_db()
        _run("category", "add", "Trabajo")

    def teardown_method(self) -> None:
        _restore_db()

    def test_create_habit(self) -> None:
        r = _run("habit", "add", "Programar 1 hora", "-c", "Trabajo", "-d", "Una hora de código")
        assert r.returncode == 0, r.stderr
        assert "Programar 1 hora" in r.stdout

    def test_list_habits(self) -> None:
        _run("habit", "add", "Revisar emails", "-c", "Trabajo", "-d", "Diario")
        r = _run("habit", "list")
        assert r.returncode == 0
        assert "Programar 1 hora" in r.stdout or "Revisar emails" in r.stdout

    def test_search(self) -> None:
        _run("habit", "add", "Leer 20 páginas", "-c", "Trabajo")
        r = _run("search", "Leer")
        assert r.returncode == 0
        assert "Leer" in r.stdout


# ---------------------------------------------------------------------------
# Logs y today
# ---------------------------------------------------------------------------

class TestLog:
    def setup_method(self) -> None:
        _backup_db()
        _run("category", "add", "Salud")
        _run("habit", "add", "Hacer ejercicio", "-c", "Salud", "-d", "30 min")

    def teardown_method(self) -> None:
        _restore_db()

    def test_log_and_today(self) -> None:
        r = _run("log", "add", "1")
        assert r.returncode == 0, r.stderr
        assert "Registro creado" in r.stdout
        r2 = _run("today")
        assert r2.returncode == 0
        assert "Hacer ejercicio" in r2.stdout


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------

class TestStreak:
    def setup_method(self) -> None:
        _backup_db()
        _run("category", "add", "Estudio")
        _run("habit", "add", "Leer", "-c", "Estudio")
        _run("log", "add", "1", "-d", "2026-09-14")
        _run("log", "add", "1", "-d", "2026-09-15")

    def teardown_method(self) -> None:
        _restore_db()

    def test_streak_output(self) -> None:
        r = _run("streak")
        assert r.returncode == 0
        assert "Leer" in r.stdout
        assert "días" in r.stdout or "🔥" in r.stdout
