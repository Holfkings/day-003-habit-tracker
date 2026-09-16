# Habit Tracker CLI

Sistema de seguimiento de hábitos por línea de comandos. Crea categorías, registra hábitos, loguea ejecuciones diarias y consulta estadísticas de cumplimiento y streaks.

## Qué hace

- Gestionar categorías de hábitos (salud, estudio, trabajo, etc.)
- Registrar hábitos con nombre, descripción y frecuencia (diario, semanal, personalizado)
- Loguear ejecuciones diarias
- Ver estadísticas: tasa de cumplimiento 7d/30d, streaks (racha actual y más larga), registros por día
- Buscar hábitos por nombre o descripción
- Ver qué se registró hoy

## Stack

- Python 3 (stdlib only: argparse, sqlite3, datetime)
- SQLite para persistencia local
- Sin dependencias externas

## Uso

```bash
python habit.py --help
python habit.py category --help
python habit.py habit --help
python habit.py log --help
python habit.py stats
python habit.py today
python habit.py streak
```

## Persistencia

La base de datos se guarda en `~/.habit_tracker/habits.db` (SQLite). Se crea automáticamente al primer uso.

## El proyecto

Repo del [Reto #100Días](/../../) — día 003 de 100.

Días previos:
- Día 001: [day-001-k8s-deployer](https://github.com/Holfkings/day-001-k8s-deployer) — Generador de manifests K8s
- Día 002: [day-002-notes-cli](https://github.com/Holfkings/day-002-notes-cli) — Sistema de notas CLI con SQLite
