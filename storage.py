"""
storage.py — Habit Tracker CLI · Backend SQLite

Módulo de persistencia para el sistema de seguimiento de hábitos.
Usa SQLite nativo (stdlib), sin dependencias externas.

Tablas:
    categories   — Categorías de hábitos (salud, estudio, trabajo, etc.)
    habits       — Hábitos registrados con frecuencia y categoría
    habit_logs   — Registros diarios de ejecución por hábito

Comandos disponibles (expuestos vía habit.py):
    create_category, get_categories
    create_habit, get_habits, get_habit_by_id
    log_habit, get_habit_logs, get_logs_for_date
    get_habits_by_category
    get_habit_stats, get_all_stats
    get_streaks
    delete_habit, delete_category
    search_habits
"""

from __future__ import annotations

import sqlite3
import os
from datetime import date, datetime
from typing import Any


DB_PATH: str = os.path.expanduser("~/.habit_tracker/habits.db")


def _ensure_db_dir() -> None:
    """Crea el directorio de la base de datos si no existe."""
    db_dir: str = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


def _get_connection() -> sqlite3.Connection:
    """Retorna una conexión a la base de datos."""
    _ensure_db_dir()
    conn: sqlite3.Connection = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Crea las tablas si no existen. Idempotente."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            description TEXT DEFAULT '',
            frequency TEXT DEFAULT 'daily'
                CHECK(frequency IN ('daily', 'weekly', 'custom')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
                CHECK(is_active IN (0, 1)),
            FOREIGN KEY (category_id) REFERENCES categories(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            logged_at DATE NOT NULL,
            notes TEXT DEFAULT '',
            UNIQUE(habit_id, logged_at),
            FOREIGN KEY (habit_id) REFERENCES habits(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_id
            ON habit_logs(habit_id);
        CREATE INDEX IF NOT EXISTS idx_habit_logs_logged_at
            ON habit_logs(logged_at);
        CREATE INDEX IF NOT EXISTS idx_habits_category_id
            ON habits(category_id);
        """
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------


def create_category(name: str, description: str = "") -> int:
    """Crea una categoría y retorna su ID."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO categories (name, description) VALUES (?, ?)",
        (name, description),
    )
    conn.commit()
    category_id: int = cursor.lastrowid  # type: ignore[assignment]
    conn.close()
    return category_id


def get_categories() -> list[dict[str, Any]]:
    """Retorna todas las categorías activas."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, created_at FROM categories ORDER BY name")
    rows: list[sqlite3.Row] = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_category(category_id: int) -> bool:
    """Elimina una categoría. Retorna True si existía."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    deleted: int = cursor.rowcount
    conn.close()
    return deleted > 0


# ---------------------------------------------------------------------------
# Hábitos
# ---------------------------------------------------------------------------


def create_habit(
    name: str,
    category_id: int | None = None,
    description: str = "",
    frequency: str = "daily",
) -> int:
    """Crea un hábito y retorna su ID."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO habits (name, category_id, description, frequency)
           VALUES (?, ?, ?, ?)""",
        (name, category_id, description, frequency),
    )
    conn.commit()
    habit_id: int = cursor.lastrowid  # type: ignore[assignment]
    conn.close()
    return habit_id


def get_habits(active_only: bool = True) -> list[dict[str, Any]]:
    """Retorna todos los hábitos, opcionalmente solo los activos."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()

    if active_only:
        cursor.execute(
            """SELECT h.id, h.name, h.description, h.frequency,
                      h.created_at, h.is_active,
                      c.id AS category_id, c.name AS category_name
               FROM habits h
               LEFT JOIN categories c ON h.category_id = c.id
               WHERE h.is_active = 1
               ORDER BY h.name"""
        )
    else:
        cursor.execute(
            """SELECT h.id, h.name, h.description, h.frequency,
                      h.created_at, h.is_active,
                      c.id AS category_id, c.name AS category_name
               FROM habits h
               LEFT JOIN categories c ON h.category_id = c.id
               ORDER BY h.name"""
        )

    rows: list[sqlite3.Row] = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_habit_by_id(habit_id: int) -> dict[str, Any] | None:
    """Retorna un hábito por su ID, o None si no existe."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """SELECT h.id, h.name, h.description, h.frequency,
                  h.created_at, h.is_active,
                  c.id AS category_id, c.name AS category_name
           FROM habits h
           LEFT JOIN categories c ON h.category_id = c.id
           WHERE h.id = ?""",
        (habit_id,),
    )
    row: sqlite3.Row | None = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def update_habit(
    habit_id: int,
    name: str | None = None,
    category_id: int | None = None,
    description: str | None = None,
    frequency: str | None = None,
    is_active: bool | None = None,
) -> bool:
    """Actualiza campos de un hábito. Retorna True si se modificó."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()

    fields: list[str] = []
    values: list[Any] = []

    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if category_id is not None:
        fields.append("category_id = ?")
        values.append(category_id)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if frequency is not None:
        fields.append("frequency = ?")
        values.append(frequency)
    if is_active is not None:
        fields.append("is_active = ?")
        values.append(1 if is_active else 0)

    if not fields:
        conn.close()
        return False

    values.append(habit_id)
    query: str = f"UPDATE habits SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    updated: int = cursor.rowcount
    conn.close()
    return updated > 0


# ---------------------------------------------------------------------------
# Registros (logs)
# ---------------------------------------------------------------------------


def log_habit(habit_id: int, logged_at: str | date | None = None, notes: str = "") -> int:
    """
    Registra la ejecución de un hábito.
    logged_at: fecha en formato 'YYYY-MM-DD' o objeto date.
               Si es None, usa hoy.
    Retorna el ID del registro creado.
    """
    if logged_at is None:
        logged_at_str: str = date.today().isoformat()
    elif isinstance(logged_at, date):
        logged_at_str = logged_at.isoformat()
    else:
        logged_at_str = logged_at

    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO habit_logs (habit_id, logged_at, notes)
               VALUES (?, ?, ?)""",
            (habit_id, logged_at_str, notes),
        )
        conn.commit()
        log_id: int = cursor.lastrowid  # type: ignore[assignment]
    except sqlite3.IntegrityError:
        # Ya existe un registro para este hábito en esta fecha
        log_id = -1
    conn.close()
    return log_id


def get_habit_logs(habit_id: int, limit: int = 30) -> list[dict[str, Any]]:
    """Retorna los registros de un hábito, ordenados por fecha descendente."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """SELECT id, habit_id, logged_at, notes
           FROM habit_logs
           WHERE habit_id = ?
           ORDER BY logged_at DESC
           LIMIT ?""",
        (habit_id, limit),
    )
    rows: list[sqlite3.Row] = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_logs_for_date(target_date: str | date | None = None) -> list[dict[str, Any]]:
    """
    Retorna todos los registros de una fecha específica.
    Si target_date es None, usa hoy.
    """
    if target_date is None:
        target_date_str: str = date.today().isoformat()
    elif isinstance(target_date, date):
        target_date_str = target_date.isoformat()
    else:
        target_date_str = target_date

    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """SELECT hl.id, hl.habit_id, hl.logged_at, hl.notes,
                  h.name AS habit_name,
                  c.id AS category_id, c.name AS category_name
           FROM habit_logs hl
           JOIN habits h ON hl.habit_id = h.id
           LEFT JOIN categories c ON h.category_id = c.id
           WHERE hl.logged_at = ?
           ORDER BY h.name""",
        (target_date_str,),
    )
    rows: list[sqlite3.Row] = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_logs_between(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Retorna registros entre dos fechas (inclusive)."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """SELECT hl.id, hl.habit_id, hl.logged_at, hl.notes,
                  h.name AS habit_name,
                  c.id AS category_id, c.name AS category_name
           FROM habit_logs hl
           JOIN habits h ON hl.habit_id = h.id
           LEFT JOIN categories c ON h.category_id = c.id
           WHERE hl.logged_at >= ? AND hl.logged_at <= ?
           ORDER BY hl.logged_at DESC, h.name""",
        (start_date, end_date),
    )
    rows: list[sqlite3.Row] = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Búsqueda
# ---------------------------------------------------------------------------


def search_habits(query: str) -> list[dict[str, Any]]:
    """Busca hábitos por nombre o descripción."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    search_term: str = f"%{query}%"
    cursor.execute(
        """SELECT h.id, h.name, h.description, h.frequency,
                  h.created_at, h.is_active,
                  c.id AS category_id, c.name AS category_name
           FROM habits h
           LEFT JOIN categories c ON h.category_id = c.id
           WHERE h.is_active = 1
             AND (h.name LIKE ? OR h.description LIKE ?)
           ORDER BY h.name""",
        (search_term, search_term),
    )
    rows: list[sqlite3.Row] = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_habits_by_category(category_id: int) -> list[dict[str, Any]]:
    """Retorna hábitos de una categoría específica."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """SELECT h.id, h.name, h.description, h.frequency,
                  h.created_at, h.is_active,
                  c.id AS category_id, c.name AS category_name
           FROM habits h
           LEFT JOIN categories c ON h.category_id = c.id
           WHERE h.category_id = ?
           ORDER BY h.name""",
        (category_id,),
    )
    rows: list[sqlite3.Row] = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------


def get_habit_stats(habit_id: int) -> dict[str, Any]:
    """
    Retorna estadísticas de un hábito:
    - total_logs: total de registros
    - streak_current: racha actual de días consecutivos
    - streak_longest: racha más larga registrada
    - last_logged: última fecha registrada
    - days_since_last: días desde el último registro
    - completion_rate_7d: % de cumplimiento en los últimos 7 días
    """
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()

    # Total de logs y última fecha
    cursor.execute(
        """SELECT COUNT(*) AS total,
                  MAX(logged_at) AS last_logged
           FROM habit_logs
           WHERE habit_id = ?""",
        (habit_id,),
    )
    row: sqlite3.Row | None = cursor.fetchone()
    if row is None or row["total"] == 0:
        conn.close()
        return {
            "total_logs": 0,
            "streak_current": 0,
            "streak_longest": 0,
            "last_logged": None,
            "days_since_last": None,
            "completion_rate_7d": 0.0,
            "completion_rate_30d": 0.0,
        }

    total_logs: int = row["total"]  # type: ignore[assignment]
    last_logged_str: str | None = row["last_logged"]  # type: ignore[assignment]

    # Streak actual: contar desde hoy hacia atrás sin saltos
    if last_logged_str is not None:
        last_date: date = datetime.strptime(last_logged_str, "%Y-%m-%d").date()
        today: date = date.today()
        days_since: int = (today - last_date).days
    else:
        days_since = None

    # Streak actual: contar desde hoy hacia atrás sin saltos
    # Usamos un enfoque iterativo simple: contar días consecutivos desde hoy
    streak_current: int = 0
    if last_logged_str is not None:
        check_date: date = date.today()
        while True:
            check_str: str = check_date.isoformat()
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM habit_logs WHERE habit_id = ? AND logged_at = ?",
                (habit_id, check_str),
            )
            row_check: sqlite3.Row | None = cursor.fetchone()
            cnt: int = row_check["cnt"] if row_check else 0
            if cnt > 0:
                streak_current += 1
                check_date = check_date.replace(day=check_date.day - 1)
            else:
                break

    # Streak más larga: contar días únicos consecutivos en el histórico
    cursor.execute(
        "SELECT DISTINCT logged_at FROM habit_logs WHERE habit_id = ? ORDER BY logged_at",
        (habit_id,),
    )
    dates_list: list[sqlite3.Row] = cursor.fetchall()
    if dates_list:
        streak_longest = 1
        current_streak = 1
        prev_date: date = datetime.strptime(dates_list[0]["logged_at"], "%Y-%m-%d").date()
        for row_d in dates_list[1:]:
            curr_date: date = datetime.strptime(row_d["logged_at"], "%Y-%m-%d").date()
            delta: int = (curr_date - prev_date).days
            if delta == 1:
                current_streak += 1
                if current_streak > streak_longest:
                    streak_longest = current_streak
            elif delta > 1:
                current_streak = 1
            prev_date = curr_date
    else:
        streak_longest = 0

    # Tasa de cumplimiento últimos 7 y 30 días
    today_str: str = date.today().isoformat()
    seven_days_ago: str = (date.today().replace(day=date.today().day - 7) if date.today().day > 7 else date.today()).isoformat()
    # Manejo simple de fechas relativas
    from datetime import timedelta
    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()

    cursor.execute(
        "SELECT COUNT(DISTINCT logged_at) AS days_logged FROM habit_logs WHERE habit_id = ? AND logged_at >= ?",
        (habit_id, seven_days_ago),
    )
    row_7d: sqlite3.Row | None = cursor.fetchone()
    days_logged_7d: int = row_7d["days_logged"] if row_7d else 0
    expected_7d: int = 7
    completion_7d: float = (days_logged_7d / expected_7d * 100) if expected_7d > 0 else 0.0

    cursor.execute(
        "SELECT COUNT(DISTINCT logged_at) AS days_logged FROM habit_logs WHERE habit_id = ? AND logged_at >= ?",
        (habit_id, thirty_days_ago),
    )
    row_30d: sqlite3.Row | None = cursor.fetchone()
    days_logged_30d: int = row_30d["days_logged"] if row_30d else 0
    expected_30d: int = 30
    completion_30d: float = (days_logged_30d / expected_30d * 100) if expected_30d > 0 else 0.0

    conn.close()

    return {
        "total_logs": total_logs,
        "streak_current": streak_current,
        "streak_longest": streak_longest,
        "last_logged": last_logged_str,
        "days_since_last": days_since,
        "completion_rate_7d": round(completion_7d, 1),
        "completion_rate_30d": round(completion_30d, 1),
    }


def get_all_stats() -> list[dict[str, Any]]:
    """Retorna estadísticas de todos los hábitos activos."""
    habits: list[dict[str, Any]] = get_habits(active_only=True)
    result: list[dict[str, Any]] = []
    for habit in habits:
        stats: dict[str, Any] = get_habit_stats(habit["id"])
        stats["habit_name"] = habit["name"]
        stats["category_name"] = habit.get("category_name", "")
        result.append(stats)
    return result


# ---------------------------------------------------------------------------
# Eliminación
# ---------------------------------------------------------------------------


def delete_habit(habit_id: int) -> bool:
    """Elimina un hábito y todos sus registros. Retorna True si existía."""
    conn: sqlite3.Connection = _get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    deleted: int = cursor.rowcount
    conn.close()
    return deleted > 0


# ---------------------------------------------------------------------------
# Formato para CLI
# ---------------------------------------------------------------------------


def format_habit(habit: dict[str, Any]) -> str:
    """Formatea un hábito para salida en CLI."""
    cat: str = habit.get("category_name", "Sin categoría")
    active: str = "✓" if habit.get("is_active", 1) else "✗"
    return (
        f"  [{active}] {habit['name']}\n"
        f"       ID: {habit['id']} | Categoría: {cat}\n"
        f"       Frecuencia: {habit.get('frequency', 'daily')} | "
        f"Creado: {habit.get('created_at', 'N/A')}"
    )


def format_stat(stat: dict[str, Any]) -> str:
    """Formatea estadísticas de un hábito para salida en CLI."""
    lines: list[str] = [
        f"  Hábito: {stat.get('habit_name', 'N/A')}",
        f"  Categoría: {stat.get('category_name', 'Sin categoría')}",
        f"  █ Total de registros: {stat.get('total_logs', 0)}",
        f"  🔥 Racha actual: {stat.get('streak_current', 0)} días",
        f"  🏆 Racha más larga: {stat.get('streak_longest', 0)} días",
    ]
    if stat.get("last_logged"):
        lines.append(f"  📅 Último registro: {stat['last_logged']}")
    if stat.get("days_since_last") is not None:
        lines.append(f"  ⏱  Días desde último registro: {stat['days_since_last']}")
    lines.extend([
        f"  📊 Tasa 7 días: {stat.get('completion_rate_7d', 0)}%",
        f"  📊 Tasa 30 días: {stat.get('completion_rate_30d', 0)}%",
    ])
    return "\n".join(lines)
