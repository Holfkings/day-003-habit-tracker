#!/usr/bin/env python3
"""
habit.py — Habit Tracker CLI

Sistema de seguimiento de hábitos por línea de comandos.
Registra hábitos, registra ejecuciones diarias, y muestra
estadísticas de cumplimiento, streaks, y resúmenes por categoría.

Uso:
    python habit.py --help
    python habit.py <comando> [opciones]

Comandos:
    category     Gestionar categorías de hábitos
    habit        Gestionar hábitos
    log          Registrar ejecución de un hábito
    stats        Ver estadísticas de hábitos
    list         Listar hábitos registrados
    search       Buscar hábitos por nombre o descripción
    today        Ver qué se registró hoy
    streak       Ver streaks de hábitos
    delete       Eliminar hábito o categoría
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from storage import (  # noqa: E402
    init_db,
    create_category,
    get_categories,
    delete_category,
    create_habit,
    get_habits,
    get_habit_by_id,
    update_habit,
    log_habit,
    get_habit_logs,
    get_logs_for_date,
    get_habits_by_category,
    search_habits,
    get_habit_stats,
    get_all_stats,
    delete_habit,
    format_habit,
    format_stat,
)


def _ensure_db() -> None:
    """Inicializa la base de datos si no existe."""
    init_db()


def cmd_category_create(args: argparse.Namespace) -> None:
    """Crear una nueva categoría."""
    _ensure_db()
    cat_id: int = create_category(args.name, args.description)
    print(f"✓ Categoría creada: '{args.name}' (ID: {cat_id})")


def cmd_category_list(args: argparse.Namespace) -> None:
    """Listar todas las categorías."""
    _ensure_db()
    categories: list[dict[str, Any]] = get_categories()
    if not categories:
        print("No hay categorías registradas.")
        return
    print(f"\\n📁 Categorías ({len(categories)}):")
    for cat in categories:
        print(f"  [{cat['id']}] {cat['name']}")
        if cat.get("description"):
            print(f"      {cat['description']}")


def cmd_category_delete(args: argparse.Namespace) -> None:
    """Eliminar una categoría."""
    _ensure_db()
    if delete_category(args.id):
        print(f"✓ Categoría {args.id} eliminada.")
    else:
        print(f"✗ Categoría {args.id} no encontrada.")


# ---------------------------------------------------------------------------
# Hábitos
# ---------------------------------------------------------------------------


def cmd_habit_create(args: argparse.Namespace) -> None:
    """Crear un nuevo hábito."""
    _ensure_db()

    category_id: int | None = None
    if args.category and args.category != "ninguna":
        categories: list[dict[str, Any]] = get_categories()
        cat_map: dict[str, int] = {c["name"].lower(): c["id"] for c in categories}
        if args.category.lower() in cat_map:
            category_id = cat_map[args.category.lower()]

    habit_id: int = create_habit(
        name=args.name,
        category_id=category_id,
        description=args.description or "",
        frequency=args.frequency or "daily",
    )
    print(f"✓ Hábito creado: '{args.name}' (ID: {habit_id})")


def cmd_habit_list(args: argparse.Namespace) -> None:
    """Listar todos los hábitos."""
    _ensure_db()
    habits: list[dict[str, Any]] = get_habits(active_only=not args.all)
    if not habits:
        print("No hay hábitos registrados.")
        return

    print(f"\\n📋 Hábitos ({len(habits)}):")
    print("─" * 50)
    for habit in habits:
        print(format_habit(habit))
        print()


def cmd_habit_show(args: argparse.Namespace) -> None:
    """Mostrar un hábito específico."""
    _ensure_db()
    habit: dict[str, Any] | None = get_habit_by_id(args.id)
    if habit is None:
        print(f"✗ Hábito {args.id} no encontrado.")
        return
    print(format_habit(habit))
    print()


def cmd_habit_update(args: argparse.Namespace) -> None:
    """Actualizar un hábito existente."""
    _ensure_db()

    kwargs: dict[str, Any] = {}
    if args.name:
        kwargs["name"] = args.name
    if args.category and args.category != "ninguna":
        categories: list[dict[str, Any]] = get_categories()
        cat_map: dict[str, int] = {c["name"].lower(): c["id"] for c in categories}
        if args.category.lower() in cat_map:
            kwargs["category_id"] = cat_map[args.category.lower()]
    if args.description is not None:
        kwargs["description"] = args.description
    if args.frequency:
        kwargs["frequency"] = args.frequency
    if args.active is not None:
        kwargs["is_active"] = args.active

    if update_habit(args.id, **kwargs):
        print(f"✓ Hábito {args.id} actualizado.")
    else:
        print(f"✗ Hábito {args.id} no encontrado.")


def cmd_habit_stats(args: argparse.Namespace) -> None:
    """Ver estadísticas de un hábito."""
    _ensure_db()
    habit: dict[str, Any] | None = get_habit_by_id(args.id)
    if habit is None:
        print(f"✗ Hábito {args.id} no encontrado.")
        return

    stats: dict[str, Any] = get_habit_stats(args.id)
    stats["habit_name"] = habit["name"]
    stats["category_name"] = habit.get("category_name", "")
    print(format_stat(stats))


def cmd_habit_streaks(args: argparse.Namespace) -> None:
    """Ver streaks de todos los hábitos."""
    _ensure_db()
    stats_list: list[dict[str, Any]] = get_all_stats()
    if not stats_list:
        print("No hay hábitos registrados.")
        return

    print("\\n🔥 Streaks de hábitos:")
    print("─" * 50)
    for stat in stats_list:
        streak: int = stat.get("streak_current", 0)
        name: str = stat.get("habit_name", "N/A")
        longest: int = stat.get("streak_longest", 0)
        print(f"  {name}: {streak} días 🔥 (máx: {longest})")


def cmd_habit_logs(args: argparse.Namespace) -> None:
    """Ver registros de un hábito."""
    _ensure_db()
    habit: dict[str, Any] | None = get_habit_by_id(args.id)
    if habit is None:
        print(f"✗ Hábito {args.id} no encontrado.")
        return

    logs: list[dict[str, Any]] = get_habit_logs(args.id, limit=args.limit)
    if not logs:
        print(f"No hay registros para '{habit['name']}'.")
        return

    print(f"\\n📝 Registros de '{habit['name']}':")
    for log in logs:
        print(f"  {log['logged_at']} — {log.get('notes', '(sin notas)')}")


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


def cmd_log_today(args: argparse.Namespace) -> None:
    """Ver qué se registró hoy."""
    _ensure_db()
    today_logs: list[dict[str, Any]] = get_logs_for_date()
    if not today_logs:
        print("No hay registros para hoy.")
        return

    print("\\n📋 Registros de hoy:")
    print("─" * 50)
    for log in today_logs:
        notes: str = log.get("notes", "") or "(sin notas)"
        print(f"  [{log['habit_name']}] {log['logged_at']} — {notes}")


def cmd_log_register(args: argparse.Namespace) -> None:
    """Registrar ejecución de un hábito."""
    _ensure_db()
    habit: dict[str, Any] | None = get_habit_by_id(args.habit_id)
    if habit is None:
        print(f"✗ Hábito {args.habit_id} no encontrado.")
        return

    log_id: int = log_habit(
        habit_id=args.habit_id,
        logged_at=args.date,
        notes=args.notes or "",
    )

    if log_id == -1:
        print(f"⚠ Ya registraste este hábito en {args.date or 'hoy'}.")
    else:
        print(f"✓ Registro creado (ID: {log_id}) para '{habit['name']}'")


# ---------------------------------------------------------------------------
# Búsqueda
# ---------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> None:
    """Buscar hábitos por nombre o descripción."""
    _ensure_db()
    results: list[dict[str, Any]] = search_habits(args.query)
    if not results:
        print(f"No se encontraron hábitos que coincidan con '{args.query}'.")
        return

    print(f"\\n🔍 Resultados para '{args.query}' ({len(results)} encontrados):")
    for habit in results:
        print(format_habit(habit))
        print()


def cmd_category_habits(args: argparse.Namespace) -> None:
    """Ver hábitos de una categoría específica."""
    _ensure_db()
    habits: list[dict[str, Any]] = get_habits_by_category(args.category_id)
    if not habits:
        print(f"No hay hábitos en la categoría {args.category_id}.")
        return

    cat = get_categories()
    cat_name = next((c["name"] for c in cat if c["id"] == args.category_id), "Desconocida")

    print(f"\\n📁 Hábitos en '{cat_name}':")
    for habit in habits:
        print(format_habit(habit))
        print()


# ---------------------------------------------------------------------------
# Eliminación
# ---------------------------------------------------------------------------


def cmd_delete_habit(args: argparse.Namespace) -> None:
    """Eliminar un hábito."""
    _ensure_db()
    habit: dict[str, Any] | None = get_habit_by_id(args.id)
    if habit is None:
        print(f"✗ Hábito {args.id} no encontrado.")
        return

    if args.confirm:
        if delete_habit(args.id):
            print(f"✓ Hábito '{habit['name']}' eliminado.")
        else:
            print(f"✗ No se pudo eliminar el hábito.")
    else:
        print(f"⚠ Para eliminar '{habit['name']}' usa --confirm")


def cmd_delete_category(args: argparse.Namespace) -> None:
    """Eliminar una categoría."""
    _ensure_db()
    categories: list[dict[str, Any]] = get_categories()
    cat: dict[str, Any] | None = next((c for c in categories if c["id"] == args.id), None)
    if cat is None:
        print(f"✗ Categoría {args.id} no encontrada.")
        return

    if args.confirm:
        if delete_category(args.id):
            print(f"✓ Categoría '{cat['name']}' eliminada.")
        else:
            print(f"✗ No se pudo eliminar la categoría.")
    else:
        print(f"⚠ Para eliminar '{cat['name']}' usa --confirm")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="habit",
        description="Habit Tracker CLI — Sistema de seguimiento de hábitos",
    )
    subparsers: argparse._SubParsersAction = parser.add_subparsers(
        dest="command", help="Comando a ejecutar"
    )

    # category
    cat_parser: argparse.ArgumentParser = subparsers.add_parser(
        "category", help="Gestionar categorías"
    )
    cat_sub: argparse._SubParsersAction = cat_parser.add_subparsers(dest="cat_cmd")

    cat_create: argparse.ArgumentParser = cat_sub.add_parser("add", help="Agregar categoría")
    cat_create.add_argument("name", help="Nombre de la categoría")
    cat_create.add_argument("-d", "--description", default="", help="Descripción de la categoría")
    cat_create.set_defaults(func=cmd_category_create)

    cat_list: argparse.ArgumentParser = cat_sub.add_parser("list", help="Listar categorías")
    cat_list.set_defaults(func=cmd_category_list)

    cat_delete: argparse.ArgumentParser = cat_sub.add_parser("delete", help="Eliminar categoría")
    cat_delete.add_argument("id", type=int, help="ID de la categoría")
    cat_delete.set_defaults(func=cmd_category_delete)

    # habit
    habit_parser: argparse.ArgumentParser = subparsers.add_parser(
        "habit", help="Gestionar hábitos"
    )
    habit_sub: argparse._SubParsersAction = habit_parser.add_subparsers(dest="habit_cmd")

    h_create: argparse.ArgumentParser = habit_sub.add_parser("add", help="Crear hábito")
    h_create.add_argument("name", help="Nombre del hábito")
    h_create.add_argument("-c", "--category", default="ninguna", help="Categoría del hábito")
    h_create.add_argument("-d", "--description", default="", help="Descripción del hábito")
    h_create.add_argument("-f", "--frequency", default="daily", help="Frecuencia: daily, weekly")
    h_create.set_defaults(func=cmd_habit_create)

    h_list: argparse.ArgumentParser = habit_sub.add_parser("list", help="Listar hábitos")
    h_list.add_argument("--all", action="store_true", help="Incluir hábitos inactivos")
    h_list.set_defaults(func=cmd_habit_list)

    h_show: argparse.ArgumentParser = habit_sub.add_parser("show", help="Mostrar hábito")
    h_show.add_argument("id", type=int, help="ID del hábito")
    h_show.set_defaults(func=cmd_habit_show)

    h_update: argparse.ArgumentParser = habit_sub.add_parser("update", help="Actualizar hábito")
    h_update.add_argument("id", type=int, help="ID del hábito")
    h_update.add_argument("-n", "--name", help="Nuevo nombre")
    h_update.add_argument("-c", "--category", help=" Nueva categoría")
    h_update.add_argument("-d", "--description", help="Nueva descripción")
    h_update.add_argument("-f", "--frequency", help="Nueva frecuencia")
    h_update.add_argument("--active", type=lambda x: x.lower() in ("1", "true", "sí", "si"), help="Activo/inactivo")
    h_update.set_defaults(func=cmd_habit_update)

    h_stats: argparse.ArgumentParser = habit_sub.add_parser("stats", help="Estadísticas de un hábito")
    h_stats.add_argument("id", type=int, help="ID del hábito")
    h_stats.set_defaults(func=cmd_habit_stats)

    h_streaks: argparse.ArgumentParser = habit_sub.add_parser("streaks", help="Ver streaks de todos los hábitos")
    h_streaks.set_defaults(func=cmd_habit_streaks)

    h_logs: argparse.ArgumentParser = habit_sub.add_parser("logs", help="Registros de un hábito")
    h_logs.add_argument("id", type=int, help="ID del hábito")
    h_logs.add_argument("-l", "--limit", type=int, default=30, help="Límite de registros a mostrar")
    h_logs.set_defaults(func=cmd_habit_logs)

    # log
    log_parser: argparse.ArgumentParser = subparsers.add_parser(
        "log", help="Registrar ejecución de un hábito"
    )
    log_sub: argparse._SubParsersAction = log_parser.add_subparsers(dest="log_cmd")

    log_today: argparse.ArgumentParser = log_sub.add_parser("today", help="Ver registros de hoy")
    log_today.set_defaults(func=cmd_log_today)

    log_reg: argparse.ArgumentParser = log_sub.add_parser("add", help="Registrar ejecución")
    log_reg.add_argument("habit_id", type=int, help="ID del hábito a registrar")
    log_reg.add_argument("-d", "--date", help="Fecha (YYYY-MM-DD). Default: hoy")
    log_reg.add_argument("-n", "--notes", default="", help="Notas del registro")
    log_reg.set_defaults(func=cmd_log_register)

    # search
    search_parser: argparse.ArgumentParser = subparsers.add_parser(
        "search", help="Buscar hábitos"
    )
    search_parser.add_argument("query", help="Texto a buscar")
    search_parser.set_defaults(func=cmd_search)

    # today
    today_parser: argparse.ArgumentParser = subparsers.add_parser(
        "today", help="Ver registros de hoy"
    )
    today_parser.set_defaults(func=cmd_log_today)

    # streak
    streak_parser: argparse.ArgumentParser = subparsers.add_parser(
        "streak", help="Ver streaks de hábitos"
    )
    streak_parser.set_defaults(func=cmd_habit_streaks)

    # delete
    delete_parser: argparse.ArgumentParser = subparsers.add_parser(
        "delete", help="Eliminar hábito o categoría"
    )
    del_sub: argparse._SubParsersAction = delete_parser.add_subparsers(dest="del_cmd")

    del_habit: argparse.ArgumentParser = del_sub.add_parser("habit", help="Eliminar hábito")
    del_habit.add_argument("id", type=int, help="ID del hábito")
    del_habit.add_argument("-c", "--confirm", action="store_true", help="Confirmar eliminación")
    del_habit.set_defaults(func=cmd_delete_habit)

    del_cat: argparse.ArgumentParser = del_sub.add_parser("category", help="Eliminar categoría")
    del_cat.add_argument("id", type=int, help="ID de la categoría")
    del_cat.add_argument("-c", "--confirm", action="store_true", help="Confirmar eliminación")
    del_cat.set_defaults(func=cmd_delete_category)

    # category-habits
    cat_hab_parser: argparse.ArgumentParser = subparsers.add_parser(
        "category-habits", help="Ver hábitos de una categoría"
    )
    cat_hab_parser.add_argument("category_id", type=int, help="ID de la categoría")
    cat_hab_parser.set_defaults(func=cmd_category_habits)

    return parser


def main() -> None:
    """Punto de entrada principal."""
    parser: argparse.ArgumentParser = _build_parser()
    args: argparse.Namespace = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if hasattr(args, "func"):
            args.func(args)
        else:
            print(f"Comando no reconocido: {args.command}")
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\\n⚠ Operación cancelada.")
        sys.exit(130)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
