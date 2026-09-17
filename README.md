<div align="center">

# 📊 Habit Tracker CLI

### Track habits · Daily logs · Statistics · Streaks · SQLite

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=database&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/CLI-Terminal-grey?style=for-the-badge&logo=gnubash&logoColor=white" alt="CLI">
  <img src="https://img.shields.io/badge/Zero_Dependencies-✓-green?style=for-the-badge&logo=package&logoColor=white" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Tests-6-9b59b6?style=for-the-badge&logo=pytest&logoColor=white" alt="6 Tests">
</p>

</div>

---

## ✨ What It Does

A command-line habit tracking system. Create categories, register habits, log daily completions, and view detailed statistics.

| Feature | Description |
|---------|-------------|
| **📂 Categories** | Organize habits (health, study, work, etc.) |
| **✅ Habits** | Register with name, description, frequency |
| **📝 Daily logs** | Record daily completions |
| **📈 Statistics** | 7d/30d compliance rate, streaks |
| **🔥 Streaks** | Current streak + longest streak |
| **🔍 Search** | Find habits by name or description |
| **📅 Today** | See what's logged today |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3 (stdlib only) |
| **Database** | SQLite (`sqlite3` stdlib) |
| **CLI** | `argparse` (stdlib) |
| **Date handling** | `datetime` (stdlib) |
| **Dependencies** | **Zero** — pure stdlib |

---

## 📦 Project Structure

```text
day-003-habit-tracker/
├── habit.py           # Main CLI — all commands
├── db.py              # Database layer — SQLite operations
├── tests/
│   └── test_habit.py  # Automated tests (6 tests)
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/Holfkings/day-003-habit-tracker.git
cd day-003-habit-tracker

# Database auto-creates on first use
# No installation needed
```

---

## 📖 Usage

```bash
# Help
python habit.py --help
python habit.py category --help
python habit.py habit --help
python habit.py log --help

# Commands
python habit.py stats        # View statistics
python habit.py today        # Today's logged habits
python habit.py streak       # View streaks
```

### Workflow Example

```bash
# 1. Create a category
python habit.py category add "Health"

# 2. Add a habit
python habit.py habit add "Morning run" --category "Health" --freq daily

# 3. Log today
python habit.py log "Morning run"

# 4. Check stats
python habit.py stats

# 5. See today's progress
python habit.py today
```

---

## 📊 Statistics

| Metric | Description |
|--------|-------------|
| **7d rate** | Compliance rate last 7 days |
| **30d rate** | Compliance rate last 30 days |
| **Current streak** | Consecutive days logged |
| **Longest streak** | Best streak ever |
| **Records by day** | History of daily completions |

---

## 🧪 Tests

```bash
# Run all tests (6 tests)
python3 -m pytest tests/ -v
```

Tests use a temporary database — your real data stays safe.

---

## 📂 Database

| Detail | Info |
|--------|------|
| **Location** | `~/.habit_tracker/habits.db` |
| **Engine** | SQLite |
| **Creation** | Automatic on first use |
| **Persistence** | Survives restarts |

---

## 🎯 Why This Project

Part of the **#100Days Challenge** — building a real project every day for 100 days.

This project demonstrates:
- ✅ Solid Python — CLI design, SQLite schema, date handling
- ✅ Data modeling — categories, habits, logs relationship
- ✅ Statistics computation — 7d/30d rates, streak calculation
- ✅ Testing culture — 6 automated tests covering core logic
- ✅ Zero dependencies — runs anywhere Python 3 is available

---

## 🔜 Future Improvements

- [ ] Edit habits
- [ ] Delete habits
- [ ] Export data (CSV, Markdown)
- [ ] Habit templates
- [ ] Reminders/notifications
- [ ] Web interface
- [ ] Sync across devices

---

<div align="center">

**Day 003/100** of the [#100Days Challenge](https://github.com/Holfkings)

Previous:
- Day 001: [K8s Deploy Generator](https://github.com/Holfkings/day-001-k8s-deployer)
- Day 002: [Notes CLI](https://github.com/Holfkings/day-002-notes-cli)

<p align="center" style="color: #888; font-size: 0.85em; margin-top: 24px;">
  Built by [@Holfkings](https://github.com/Holfkings) · Python + SQLite · Clean code
</p>

</div>
